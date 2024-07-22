from django.contrib.auth.models import User
from django.forms import ModelForm
from .models import Post, Comment
from django import forms


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class PostCreateForm(ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'}),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': '10', 'cols': '20'}),
        }


class PostDeleteForm(ModelForm):

    class Meta:
        model = Post
        fields = []
