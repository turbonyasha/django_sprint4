from django.db.models import Count
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from .models import Post, Comment


def posts_request_method(posts):
    return (
        posts
        .annotate(comment_count=Count('comments'))
        .select_related('author', 'location', 'category')
        .order_by(*Post._meta.ordering)
    )


def get_published_posts(posts=Post.objects.all(), add_unpublished=False):
    if add_unpublished:
        return posts_request_method(posts)
    return (
        posts_request_method(posts).filter(
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True
        )
    )


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин для подтвеждения возможностей
    пользователя на удаление и редактирование.
    """

    def test_func(self):
        return self.get_object().author == self.request.user


class CommentMixin:
    """Миксин для действий с комментариями."""

    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.comment = self.get_object()
        if self.comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.comment.id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )
