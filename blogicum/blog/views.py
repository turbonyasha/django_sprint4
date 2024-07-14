from datetime import datetime

from django.shortcuts import get_object_or_404, render

from .models import Post, Category


def get_published_posts(posts=Post.objects.all()):
    return posts.filter(
        pub_date__lte=datetime.now(),
        category__is_published=True,
        is_published=True
    )


def index(request):
    return render(request, 'blog/index.html', {
        'post_list': get_published_posts()[0:5]
    })


def post_detail(request, post_id):
    return render(request, 'blog/detail.html', {
        'post': get_object_or_404(
            get_published_posts(),
            pk=post_id
        ),
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category.objects.all(),
        slug=category_slug,
        is_published=True
    )
    return render(request, 'blog/category.html', {
        'post_list': get_published_posts(category.posts.all()),
        'category': category,
    })
