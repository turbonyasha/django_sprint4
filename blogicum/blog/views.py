from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostCreateForm, PostDeleteForm, UserProfileForm
from .models import Category, Comment, Post
from .utils import (
    CommentObjectAndURLMixin,
    PAGINATION_COUNT,
    OnlyAuthorMixin,
    PaginationMixin,
    get_published_posts,
)


User = get_user_model()


class PostListView(ListView):
    """CBV для отображения списка всех постов."""

    model = Post
    ordering = 'id'
    template_name = 'blog/index.html'
    paginate_by = PAGINATION_COUNT

    def get_queryset(self):
        return get_published_posts().order_by('-pub_date')


class PostCreateView(LoginRequiredMixin, CreateView):
    """CBV для создания нового поста."""

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
    """CBV для просмотра отдельного поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        if post.author != self.request.user and not post.is_published:
            raise Http404('Пост не доступен для просмотра')
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.prefetch_related(
            'post'
        ).filter(
            post=post
        )
        return context


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    """CBV для редактирования поста."""

    model = Post
    form_class = PostCreateForm
    template_name = 'blog/create.html'

    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs.get('post_id')}
        )
    
    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """CBV для удаления поста."""

    model = Post
    success_url = reverse_lazy('blog:index')
    form_class = PostDeleteForm
    template_name = 'blog/create.html'
    
    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )
    
    def form_valid(self, form):
        return super(PostDeleteForm, self).form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class(instance=self.object)
        context['form'] = form
        return context
    
    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class CategoryView(ListView):
    """CBV для отображения списка всех постов
    в определенной категории."""

    model = Post
    ordering = 'id'
    template_name = 'blog/category.html'
    paginate_by = PAGINATION_COUNT
    slug_url_kwarg = 'category_slug'
    context_object_name = 'category'

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return get_published_posts().filter(category=self.category).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
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


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    CBV для редактирования профиля пользователя.
    """

    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return User.objects.get(username=self.request.user.username)
    
    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'profile': self.object.username}
        )


class CommentCreateView(
    CommentObjectAndURLMixin,
    LoginRequiredMixin,
    CreateView
):
    """
    CBV для создания комментария от пользователя.
    """

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.comment_post = get_object_or_404(
            Post,
            pk=kwargs.get('post_id')
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.comment_post
        return super().form_valid(form)


class CommentUpdateView(CommentObjectAndURLMixin, UpdateView):
    """
    CBV для редактирования комментария от пользователя.
    """

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        comment_post = self.get_object()
        if comment_post.author != self.request.user:
            return redirect('blog:post_detail', post_id=comment_post.id)
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(CommentObjectAndURLMixin, DeleteView):
    """
    CBV для удаления комментария от пользователя.
    """
    model = Comment
    template_name = 'blog/comment.html'
