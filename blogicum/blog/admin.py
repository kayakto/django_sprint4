from django.contrib import admin  # type: ignore
from .models import Category, Location, Post

admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post)
