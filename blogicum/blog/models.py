from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

TITLES_LENGTH = 256

VISIBLE_TITLES_LENGTH = 25


class CreatedAtIsPublishedModel(models.Model):
    is_published = models.BooleanField(default=True,
                                       verbose_name='Опубликовано',
                                       help_text=(
                                           'Снимите галочку, чтобы '
                                           'скрыть публикацию.')
                                       )
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Добавлено')

    class Meta:
        abstract = True


class Category(CreatedAtIsPublishedModel):
    title = models.CharField('Заголовок', max_length=TITLES_LENGTH)
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL;'
            ' разрешены символы латиницы, цифры, дефис '
            'и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:VISIBLE_TITLES_LENGTH]


class Location(CreatedAtIsPublishedModel):
    name = models.CharField(
        'Название места',
        max_length=TITLES_LENGTH,
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:VISIBLE_TITLES_LENGTH]


class Post(CreatedAtIsPublishedModel):
    title = models.CharField('Название', max_length=TITLES_LENGTH)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время '
            'в будущем — можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    location = models.ForeignKey(
        Location,
        verbose_name='Местоположение',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='posts',
        on_delete=models.SET_NULL,
        null=True
    )
    image = models.ImageField(
        'Фото',
        upload_to='post_images',
        blank=True
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.title[:VISIBLE_TITLES_LENGTH]


class Comment(models.Model):
    text = models.TextField('Комментарий')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return (
            f'{self.post}, {self.author}, '
            f'{self.text[:30]}'
        )