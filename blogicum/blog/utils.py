from django.db.models import Count
from django.utils import timezone

from django.contrib.auth.mixins import UserPassesTestMixin

from .models import Post, Comment


def get_published_posts(posts=Post.objects.all()):
    return (
        posts.filter(
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True
        ).annotate(comment_count=Count('comments'))
        .select_related('author', 'location', 'category')
        .order_by('-pub_date')
    )


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин для подтвеждения возможностей
    пользователя на удаление и редактирование.
    """

    def test_func(self):
        return self.get_object().author == self.request.user
