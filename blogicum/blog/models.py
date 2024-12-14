from django.db import models  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore
from django.utils.timezone import now  # type: ignore

User = get_user_model()


class BaseModel(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        blank=False,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        'Добавлено',
        auto_now_add=True
    )

    class Meta:
        abstract = True


class Category(BaseModel):
    title = models.CharField('Заголовок', max_length=256, blank=False)
    description = models.TextField('Описание', blank=False)
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        blank=False,
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        )
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Location(BaseModel):
    name = models.CharField('Название места', max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'


class Post(BaseModel):
    title = models.CharField('Заголовок', max_length=256, blank=False)
    text = models.TextField('Текст', blank=False)
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        blank=False,
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    image = models.ImageField(
        verbose_name='Фото', blank=True, upload_to='post_images'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        verbose_name='Категория'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def is_visible(self):
        return self.is_published and self.pub_date <= now()


class Comment(BaseModel):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_at',)
