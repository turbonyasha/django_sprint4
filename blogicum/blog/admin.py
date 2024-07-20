from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Location, Post

admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post)
