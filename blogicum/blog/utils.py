from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .models import Post, Comment


def get_published_posts(posts=Post.objects.all(), filter_published=True):
    posts = posts.annotate(
        comment_count=Count('comments')
    ). select_related(
        'author', 'location', 'category'
    ).order_by(
        *Post._meta.ordering
    )
    if filter_published:
        posts = posts.filter(
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True
        )
    return posts


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
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs['post_id']]
        )
