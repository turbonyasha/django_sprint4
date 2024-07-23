from django.db.models import Count
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .models import Post, Comment


def get_published_posts(posts=Post.objects.all(), include_unpublished=False):
    on_page_posts = (
        posts
        .annotate(comment_count=Count('comments'))
        .select_related('author', 'location', 'category')
        .order_by(*Post._meta.ordering)
    )
    if not include_unpublished:
        on_page_posts = on_page_posts.filter(
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True
        )
    return on_page_posts


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
            return redirect('blog:post_detail', post_id=comment.comments__id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )
