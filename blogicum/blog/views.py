from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import Http404
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
    get_published_posts
)


class PostListView(ListView):
    """CBV для отображения списка всех постов."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.PAGINATION_COUNT
    ordering = '-pub_date'
    queryset = (
        get_published_posts()
    )


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

    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )

    def get_post(self):
        post = self.get_object()
        if post.author != self.request.user and not post.is_published:
            raise Http404("Запрошенный пост не найден.")
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

    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )

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

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return (
            get_published_posts()
            .filter(category=self.category)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileView(ListView):
    """
    CBV для отображения профиля пользователя
    и списка опубликованных им постов.
    """

    model = Post
    ordering = '-pub_date'
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    slug_field = 'username'
    slug_url_kwarg = 'profile'
    paginate_by = settings.PAGINATION_COUNT

    def get_queryset(self):
        self.user = get_object_or_404(
            User,
            username=self.kwargs[self.slug_url_kwarg]
        )
        queryset = Post.objects.filter(author=self.user)
        if self.request.user.username == self.user.username:
            return (
                queryset.annotate(comment_count=Count('comments'))
                .order_by('-pub_date')
            )
        else:
            return (
                get_published_posts().filter(author=self.user))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.user
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

    def form_valid(self, form):
        self.comment_post = get_object_or_404(
            Post, pk=self.kwargs.get('post_id')
        )
        form.instance.author = self.request.user
        form.instance.post = self.comment_post
        return super().form_valid(form)

    def get_object(self):
        return get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id'],
            post__author=self.request.user
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )


class CommentUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """CBV для редактирования комментария от пользователя."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        comment_post = self.get_object()
        if comment_post.author != self.request.user:
            return redirect('blog:post_detail', post_id=comment_post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id']
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context


class CommentDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    """CBV для удаления комментария от пользователя."""

    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        comment_post = self.get_object()
        if comment_post.author != self.request.user:
            return redirect('blog:post_detail', post_id=comment_post.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id']
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )
