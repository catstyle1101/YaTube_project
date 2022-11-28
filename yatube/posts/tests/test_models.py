from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_models_have_correct_object_names(self):
        """Проверка метода __str__ класса Group."""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_group_verbose_name(self):
        """verbose_name полей Group совпадают с ожидаемыми."""
        post = GroupModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Адрес',
            'description': 'Описание группы'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_models_have_correct_object_names(self):
        """Проверка метода __str__ класса Post."""
        post = PostModelTest.post
        expected_object_name = post.text[:settings.POST_TITLE_SHOW_LENGTH]
        self.assertEqual(expected_object_name, str(post))

    def test_post_verbose_name(self):
        """verbose_name полей Post совпадает с ожидаемыми."""
        post = PostModelTest.post
        field_verboses = {
            'group': 'Группа',
            'text': 'Текст поста',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_post_models_have_help_text(self):
        """help_text полей Post совпадает с ожидаемыми."""
        post = PostModelTest.post
        field_help_texts = {
            'group': 'Группа поста',
            'text': 'Текст поста',

        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
