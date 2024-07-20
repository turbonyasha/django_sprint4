from datetime import datetime

from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post, Category
from .forms import UserProfileForm
from django.views.generic.detail import SingleObjectMixin
from django.http import Http404
from django.urls import reverse
from .forms import PostCreateForm

User = get_user_model()

PAGINATION_COUNT = 10

def get_published_posts(posts=Post.objects.all()):
    return posts.filter(
        pub_date__lte=datetime.now(),
        category__is_published=True,
        is_published=True
    )


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user 


class PaginationMixin(SingleObjectMixin):
    """
    Миксин для пагинации на странице пользователя
    """
    paginate_by = PAGINATION_COUNT

    def get_queryset(self):
        if self.object == self.request.user:
            return self.object.posts.comment_count().order_by('-pub_date')
        return self.object.posts.all().order_by('-pub_date')
    

class PostListView(ListView):
    """CBV для отображения списка всех постов."""

    model = Post
    ordering = 'id'
    template_name = 'blog/index.html'
    paginate_by = 10


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    CBV для создания нового поста.
    Доделать: поля и условия из ТЗ
    """
    model = Post
    template_name = 'blog/create.html'
    form_class = PostCreateForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={
                'profile': self.request.user.username
            }
        )
    


class SinglePostView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'


class CategoryView(ListView):
    """CBV для отображения списка всех постов
    в определенной категории."""

    model = Post
    ordering = 'id'
    template_name = 'blog/category.html'
    paginate_by = 10
    slug_url_kwarg = 'category_slug'
    context_object_name = 'category'

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        return Post.objects.filter(category__slug=category_slug)
    # .order_by('-published_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        try:
            category = Category.objects.get(slug=category_slug)
            context['category'] = category.title  # Добавляем название категории в контекст
        except Category.DoesNotExist:
            context['category'] = 'Unknown Category'  # Обработка случая, если категория не найдена
        return context


class ProfileView(PaginationMixin, ListView):
    """
    CBV для отображения профиля пользователя
    и списка опубликованных им постов.
    """

    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'profile'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=User.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object
        return context


class ProfileEditView(OnlyAuthorMixin, UpdateView):
    """
    CBV для редактирования профиля пользователя.
    """
    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return User.objects.get(username=self.request.user.username)
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'profile': self.object.username})
    


