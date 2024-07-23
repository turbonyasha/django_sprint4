from django.contrib.auth import get_user_model
from django.db import models

MAX_LENGTH_STR = 30


User = get_user_model()


class PublishedModel(models.Model):
    """Абстракстная модель.
    Добавляет флаг is_published и created_at.
    Добавляет переменную related_name.
    """

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True


class Category(PublishedModel):
    """Класс тематических категорий."""

    title = models.CharField(
        'Заголовок',
        max_length=256,
        help_text='Максимальная длина строки — 256 символов'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title',)

    def __str__(self):
        return self.title[:MAX_LENGTH_STR]


class Location(PublishedModel):
    """Класс географических меток."""

    name = models.CharField(
        'Название места',
        max_length=256,
        help_text='Максимальная длина строки — 256 символов'
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name',)

    def __str__(self):
        return self.name[:MAX_LENGTH_STR]


class Post(PublishedModel):
    """Класс публикаций."""

    title = models.CharField(
        'Заголовок',
        max_length=256,
        help_text='Максимальная длина строки — 256 символов'
    )
    text = models.TextField(
        'Текст'
    )
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем '
                  '— можно делать отложенные публикации.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='post_images',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'

    def __str__(self):
        return self.title[:MAX_LENGTH_STR]


class Comment(PublishedModel):
    """Класс комментариев."""

    text = models.TextField('Комментарий', null=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'
