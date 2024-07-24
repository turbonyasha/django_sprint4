from django.contrib.auth.mixins import LoginRequiredMixin

from django.conf import settings
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
from .models import Category, Comment, Post, User
from .utils import (
    OnlyAuthorMixin,
    get_published_posts,
    CommentMixin
)


class PostListView(ListView):
    """CBV для отображения списка всех постов."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.PAGINATION_COUNT
    queryset = get_published_posts()


class PostCreateView(LoginRequiredMixin, CreateView):
    """CBV для создания нового поста."""

    model = Post
    template_name = 'blog/create.html'
    form_class = PostCreateForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', args=[self.request.user.username]
        )


class SinglePostView(DetailView):
    """CBV для просмотра отдельного поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_post(self):
        post = self.get_object()
        if post.author != self.request.user:
            post = get_object_or_404(
                get_published_posts(),
                pk=self.kwargs.get(self.pk_url_kwarg)
            )
        return post

    def get_context_data(self, **kwargs):
        post = self.get_post()
        return super().get_context_data(
            **kwargs,
            post=post,
            form=CommentForm(),
            comments=post.comments.prefetch_related('post')
        )


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    """CBV для редактирования поста."""

    model = Post
    form_class = PostCreateForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """CBV для удаления поста."""

    model = Post
    success_url = reverse_lazy('blog:index')
    form_class = PostDeleteForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class CategoryView(ListView):
    """
    CBV для отображения списка всех постов
    в определенной категории.
    """

    model = Post
    ordering = '-pub_date'
    template_name = 'blog/category.html'
    paginate_by = settings.PAGINATION_COUNT
    slug_url_kwarg = 'category_slug'
    context_object_name = 'category'

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs[self.slug_url_kwarg],
            is_published=True
        )

    def get_queryset(self):
        category = self.get_category()
        return (
            get_published_posts(posts=category.posts.all())
        )


class ProfileView(ListView):
    """
    CBV для отображения профиля пользователя
    и списка опубликованных им постов.
    """

    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    slug_field = 'username'
    slug_url_kwarg = 'profile'
    paginate_by = settings.PAGINATION_COUNT

    def get_author(self):
        return get_object_or_404(
            User,
            username=self.kwargs[self.slug_url_kwarg]
        )

    def get_queryset(self):
        return get_published_posts(
            posts=self.get_author().posts.all(),
            filter_published=(
                self.request.user != self.get_author()
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_author()
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """CBV для редактирования профиля пользователя."""

    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'profile': self.object.username}
        )


class CommentCreateView(
    LoginRequiredMixin,
    CreateView
):
    """CBV для создания комментария от пользователя."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    comment = None

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs.get('post_id')
        )
        return super().form_valid(form)

    def get_object(self):
        self.comment = get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id'],
        )
        return self.comment

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )


class CommentUpdateView(
    LoginRequiredMixin, OnlyAuthorMixin, CommentMixin, UpdateView
):
    """CBV для редактирования комментария от пользователя."""

    form_class = CommentForm


class CommentDeleteView(
    LoginRequiredMixin, OnlyAuthorMixin, CommentMixin, DeleteView
):
    """CBV для удаления комментария от пользователя."""

    pass
