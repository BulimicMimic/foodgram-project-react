from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import CustomUserManager


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        user = ('user', 'Пользователь')
        admin = ('admin', 'Администратор')

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=255,
        choices=Role.choices,
        default=Role.user,
    )
    objects = CustomUserManager()

    class Meta:
        ordering = ['id']
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
