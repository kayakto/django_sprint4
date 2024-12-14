from django.views.generic import TemplateView  # type: ignore
from django.shortcuts import render  # type: ignore


class About(TemplateView):
    template_name = 'pages/about.html'


class Rules(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def internal_server_error(request):
    return render(request, 'pages/500.html', status=500)  # Исправлено на 500


def csrf_failure(request):
    return render(request, 'pages/403csrf.html', status=403)
