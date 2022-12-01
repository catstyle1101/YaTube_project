
import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from http import HTTPStatus

from ..models import Comment, Group, Post
from ..forms import CommentForm, PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.another_user = User.objects.create_user(username='second')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.another_authorised_client = Client()
        self.another_authorised_client.force_login(self.another_user)
        self.unauthorised_client = Client()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'group': self.group.pk,
            'text': 'Тестовая запись',
            'image': uploaded,
        }
        self.assertTrue(PostForm(data=form_data).is_valid())
        response = self.authorised_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                args=(self.user.username,)
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая запись',
                group=self.group,
                author=self.user,
                image=f'posts/{uploaded}',
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            'text': 'Изменено',
            'group': self.group.pk,
        }
        count_posts = Post.objects.all().count()
        response = self.authorised_client.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data=form_data,
            follow=True,
        )
        pub_date_original = self.post.pub_date
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(self.post.pk,)),
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.pk,
                pk=self.post.pk,
                author=self.post.author,
                pub_date=pub_date_original,
            ).exists()
        )
        self.assertEqual(count_posts, Post.objects.all().count())

    def test_edit_post_by_not_author(self):
        """Редактирование записи недоступно не автору."""
        form_data = {
            'text': 'Изменено',
            'group': self.group.pk,
        }
        count_posts = Post.objects.all().count()
        response = self.another_authorised_client.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data=form_data,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Post.objects.filter(
                pk=self.post.pk,
                text='Тестовый текст',
                author=self.user,
                group=self.group,
                pub_date=self.post.pub_date,
            ).exists()
        )
        self.assertEqual(count_posts, Post.objects.all().count())

    def test_edit_post_by_not_authorised_user(self):
        """Редактирование записи недоступно не авторизованному пользователю."""
        form_data = {
            'text': 'Изменено',
            'group': self.group.pk,
        }
        count_posts = Post.objects.all().count()
        response = self.unauthorised_client.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, '/posts/1/')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                author=self.user,
                group=self.group,
                pub_date=self.post.pub_date,
            ).exists()
        )
        self.assertEqual(count_posts, Post.objects.all().count())

    def test_create_post_without_group(self):
        """Валидная форма создает Post, без указания Group."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
        }
        response = self.authorised_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая запись',
                author=self.user,
                group=None,
            ).exists()
        )

    def test_create_post_with_invalid_form(self):
        """Не валидная форма не создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
            'group': 123,
        }
        response = self.authorised_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='auth')

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.auth_user)
        self.post = Post.objects.create(
            author=self.auth_user,
            text='Текст поста',
            group=None,
        )

    def test_add_comment(self):
        """Валидная форма создает коментарий к Post."""
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.assertTrue(CommentForm(data=form_data).is_valid())
        count_comments = self.post.comments.count()
        response = self.authorised_client.post(
            reverse(
                'posts:add_comment',
                args=(self.post.id,)
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(count_comments + 1, self.post.comments.count())
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                args=(self.post.id,)
            ),
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.auth_user,
                post=self.post,
            ).exists()
        )
