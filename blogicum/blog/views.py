from typing import Any
from django.db.models.query import QuerySet  # type: ignore
from django.db.models import Count  # type: ignore
from django.shortcuts import get_object_or_404, redirect  # type: ignore
from django.views.generic import (ListView,  # type: ignore
                                  DetailView, CreateView,
                                  UpdateView, DeleteView)
from django.utils import timezone  # type: ignore
from django.http import Http404  # type: ignore
from django.contrib.auth.models import User  # type: ignore
from django.core.paginator import Paginator  # type: ignore
from django.urls import reverse_lazy  # type: ignore
from django.contrib.auth.mixins import LoginRequiredMixin  # type: ignore
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment


POSTS_ON_PAGE = 10


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = POSTS_ON_PAGE

    def get(self, request, *args, **kwargs):
        category_slug = self.kwargs.get('category_slug')
        self.category = get_object_or_404(Category, slug=category_slug)

        if not self.category.is_published:
            raise Http404('category is not published')

        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        current_time = timezone.now()
        category_slug = self.kwargs.get('category_slug')

        queryset = Post.objects.select_related(
            'category', 'author', 'location'
        ).filter(
            category__slug=category_slug,
            is_published=True,
            pub_date__lte=current_time
        ).order_by('-pub_date')

        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        category = self.category
        context['category'] = category
        return context


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        current_time = timezone.now()

        queryset = Post.objects.select_related(
            'category', 'author', 'location'
        ).filter(
            is_published=True,
            pub_date__lte=current_time,
            category__is_published=True
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        current_time = timezone.now()
        if (
            (self.object.pub_date > current_time)
            or (not self.object.is_published)
            or (self.object.category and not self.object.category.is_published)
        ):
            if self.request.user != self.object.author:
                raise Http404('This post is not available.')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context

    def get_queryset(self) -> QuerySet[Post]:
        return Post.objects.select_related('category', 'author', 'location')


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = '__all__'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        if request.user != post.author:
            return redirect(reverse_lazy('blog:post_detail',
                                         kwargs={'pk': self.kwargs.get('pk')}))
        return super().dispatch(request, *args, **kwargs)


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        user_posts = Post.objects.filter(
            author=self.object
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')

        if self.request.user != self.object:
            posts = user_posts.filter(is_published=True, pub_date__lte=now)
        else:
            posts = user_posts

        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page_number)
        context['profile'] = self.object
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['username', 'email', 'first_name', 'last_name']

    def get_object(self, queryset=None):
        return self.request.user

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.kwargs.get('pk')}
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_queryset(self):
        # Ограничиваем доступ к комментариям только для их авторов
        return Comment.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.post.pk}
        )

    def form_invalid(self, form):
        raise Http404('you are not author!')


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.kwargs.get('pk')})

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != self.request.user:
            raise Http404('you are not author!')
        return super().delete(request, *args, **kwargs)
