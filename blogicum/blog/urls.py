from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path(
        'posts/<int:post_id>/',
        views.SinglePostView.as_view(),
        name='post_detail'
    ),
    path(
        'category/<slug:category_slug>/',
        views.CategoryView.as_view(),
        name='category_posts'
    ),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path(
        'profile/<slug:profile>/',
        views.ProfileView.as_view(),
        name='profile'
    ),
    path(
        'auth/edit_profile/',
        views.ProfileEditView.as_view(),
        name='edit_profile'
    ),
]
