from django.db.models import Count
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from .models import Post, Comment


def get_published_posts(posts=Post.objects.all(), show_unpublished=False):
    if show_unpublished:
        return (
            posts
            .annotate(comment_count=Count('comments'))
            .select_related('author', 'location', 'category')
            .order_by(*Post._meta.ordering)
        )
    return (
        posts.filter(
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True
        ).annotate(comment_count=Count('comments'))
        .select_related('author', 'location', 'category')
        .order_by(*Post._meta.ordering)
    )


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин для подтвеждения возможностей
    пользователя на удаление и редактирование.
    """

    def test_func(self):
        return self.get_object().author == self.request.user


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    comment = None

    def dispatch(self, request, *args, **kwargs):
        if self.comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.comment.id)
        return super().dispatch(request, *args, **kwargs)

    def get_comment(self):
        self.comment = get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
        )
        return self.comment

    def get_object(self):
        return self.get_comment()

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )
