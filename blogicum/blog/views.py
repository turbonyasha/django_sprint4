from django.db.models.base import Model as Model
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse, reverse_lazy

from .forms import UserProfileForm, CommentForm, PostCreateForm
from .models import Post, Category, Comment
from .utils import (
    get_published_posts,
    OnlyAuthorMixin,
    PaginationMixin,
    CommentObjectAndURLMixin,
    PAGINATION_COUNT
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


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


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """CBV для удаления поста."""

    model = Post
    success_url = reverse_lazy('blog:index')
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect(
                'blog:post_detail',
                self.kwargs.get('post_id')
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id'),
        )


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
        category_slug = self.kwargs['category_slug']
        return (
            get_published_posts()
            .filter(category__slug=category_slug)
            .order_by('-pub_date'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        try:
            category = Category.objects.get(slug=category_slug)
            context['category'] = category.title
        except Category.DoesNotExist:
            context['category'] = 'Категория не существует'
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
