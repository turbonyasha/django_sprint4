from datetime import datetime

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import SingleObjectMixin

from .models import Post, Comment

PAGINATION_COUNT = 10


def get_published_posts(posts=Post.objects.all()):
    return posts.filter(
        pub_date__lte=datetime.now(),
        category__is_published=True,
        is_published=True
    )


class GetObjectMixin:
    """Миксин для get_object Post."""

    def get_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин для подтвеждения возможностей
    пользователя на удаление и редактирование.
    """

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PaginationMixin(SingleObjectMixin):
    """Миксин для пагинации на странице пользователя."""

    paginate_by = PAGINATION_COUNT

    def get_queryset(self):
        if self.object == self.request.user:
            return self.object.posts.order_by('-pub_date')
        return self.object.posts.all().order_by('-pub_date')


class CommentObjectAndURLMixin:
    """Миксин для комментариев."""

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise Http404('Пользователь не аутентифицирован')
        return get_object_or_404(
            Comment,
            pk=self.kwargs.get('comment_id'),
            post=get_object_or_404(Post, pk=self.kwargs.get('post_id')),
            author=self.request.user
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs.get('post_id')}
        )
