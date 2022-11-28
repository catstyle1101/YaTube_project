import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Comment, Follow, Group, Post

User = get_user_model()

COUNT_POSTS_FOR_TEST_TO_CREATE = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(BaseTest):
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
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.unauthorised_client = Client()
        cache.clear()

    def test_pages_uses_correct_templates(self):
        """Проверка шаблонов views."""
        templates_pages_names = {
            reverse('posts:index_page'): 'posts/index.html',
            reverse('posts:group_list',
                    args=(self.group.slug,)): 'posts/group_list.html',
            reverse(
                'posts:profile',
                args=(self.user.username,)): 'posts/profile.html',
            reverse('posts:post_detail',
                    args=(1,)): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    args=(1,)): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorised_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_page_context(self):
        """Проверка словаря context для view post_detail."""
        response = self.unauthorised_client.get(
            reverse('posts:post_detail', args=('1',))
        )
        post = response.context.get('post')
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.group, PostPagesTests.post.group)
        self.assertEqual(post.author, PostPagesTests.post.author)
        self.assertEqual(post.image, PostPagesTests.post.image)

    def test_edit_post_page_context(self):
        """Проверка словаря context для view edit_post,
        проверка наличия аргумента is_edit в словаре."""
        response = self.authorised_client.get(
            reverse('posts:post_edit', args=('1',))
        )
        self.assertTrue(response.context.get('is_edit'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_context(self):
        """Проверка словаря context для view post_create."""
        response = self.authorised_client.get(
            reverse('posts:post_create')
        )
        self.assertIsNone(response.context.get('is_edit'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_page_context(self):
        """Проверка словаря context для view group_list."""
        response = self.unauthorised_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        )
        post = response.context.get('post')
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, self.post.image)

    def test_author_page_context(self):
        """Проверка словаря context для view profile."""
        response = self.unauthorised_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})
        )
        post = response.context['post']
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)


class PaginatorViewsTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        bulk_list = list()
        for i in range(COUNT_POSTS_FOR_TEST_TO_CREATE):
            bulk_list.append(
                Post(
                    text=f'Теcтовый текст №{i+1}',
                    author=cls.user,
                    group=cls.group
                )
            )
        Post.objects.bulk_create(bulk_list)

    def setUp(self):
        self.client = Client()
        self.views_to_test_paginator = [
            reverse('posts:index_page'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка, что паджинатор выдает 10 Post на страницу."""
        for view in self.views_to_test_paginator:
            with self.subTest(view=view):
                response = self.client.get(view)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.COUNT_OF_POSTS_PAGINATOR)

    def test_second_page_contains_three_records(self):
        """Проверка, что паджинатор корректно выдает Post,
        если их меньше 10."""
        for view in self.views_to_test_paginator:
            with self.subTest(view=view):
                response = self.client.get(view + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    COUNT_POSTS_FOR_TEST_TO_CREATE
                    - settings.COUNT_OF_POSTS_PAGINATOR
                )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreatePostTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.another_user = User.objects.create_user(username='another')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа_2',
            slug='test-2-slug',
            description='Тестовое описание_2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        self.new_post = Post.objects.create(
            text='Тестовый 2',
            author=self.user,
            group=self.group_1,
            image=uploaded,
        )
        cache.clear()

    def test_created_post_is_on_index(self):
        """Проверка, что созданный Post появился на главной странице."""
        response = self.authorised_client.get(reverse('posts:index_page'))
        posts = response.context['page_obj']
        self.assertIn(self.new_post, posts)

    def test_created_post_is_on_group_page(self):
        """Проверка, что созданный Post появился на странице своей группы."""
        response = self.authorised_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        posts = response.context['page_obj']
        self.assertIn(self.new_post, posts)

    def test_created_post_is_on_author_page(self):
        """Проверка, что созданный Post появился на странице автора."""
        response = self.authorised_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        posts = response.context.get('page_obj')
        self.assertIn(self.new_post, posts)

    def test_created_post_is_not_in_another_group(self):
        """Проверка, что созданный Post не появился
        на странице другой группы."""
        response = self.authorised_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        posts = response.context['page_obj']
        self.assertNotIn(self.new_post, posts)

    def test_created_post_is_not_in_another_author(self):
        """Проверка, что созданный Post не появился
        на странице другого автора"""
        response = self.authorised_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.another_user.username})
        )
        posts = response.context.get('page_obj')
        self.assertNotIn(self.new_post, posts)


class CommentTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.unauthorised_client = Client()
        cache.clear()

    def test_add_comment_by_authorised_client(self):
        count_comments = self.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorised_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
        )
        self.assertEqual(count_comments + 1, self.post.comments.count())
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.id,)),
        )

    def test_add_comment_by_unauthorised_client(self):
        count_comments = self.post.comments.count()
        form_data = {
            'text': 'Тестовый',
        }
        response = self.unauthorised_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
        )
        self.assertEqual(count_comments, self.post.comments.count())

class TestCachePage(BaseTest):
    def setUp(self):
        self.authorised_user = Client()
        self.authorised_user.force_login(self.user)
        cache.clear()

    def test_index_page_uses_cache(self):
        form_data = {
            'text': 'Тестовый пост',
        }
        response = self.authorised_user.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertIsNone(response.context)
        cache.clear()
        index_page = self.authorised_user.get(reverse('posts:index_page'))
        post = index_page.context[0]['post_list'][0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, None)
        self.assertEqual(post.author, self.user)


class TestSubscribers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.first_user = User.objects.create_user(username='first')
        cls.second_user = User.objects.create_user(username='second')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=None,
        )

    def setUp(self):
        self.first_test_user = Client()
        self.first_test_user.force_login(self.first_user)
        self.second_test_user = Client()
        self.second_test_user.force_login(self.second_user)
        self.unauthorised_client = Client()
        cache.clear()

    def test_authorized_user_can_follow_author(self):
        """Авторизованный пользователь может подписаться на автора."""
        response = self.first_test_user.get(
            reverse('posts:profile_follow', args=(self.author.username,)),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Follow.objects.filter(
                user=self.first_user,
                author=self.author
            ).exists()
        )

    def test_authorized_user_can_unfollow_author(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(
            user=self.first_user,
            author=self.author
        )
        response = self.first_test_user.get(
            reverse('posts:profile_unfollow', args=(self.author.username,)),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Follow.objects.filter(
                user=self.first_user,
                author=self.author,
            ).exists()
        )

    def test_follow_index_response_correct_posts(self):
        """Посты появляются в ленте того, кто подписался на автора
        и не появляются у того, кто не подписан."""
        Follow.objects.create(
            user=self.first_user,
            author=self.author,
        )
        response = self.first_test_user.get(
            reverse('posts:follow_index'),
        )
        self.assertEqual(response.status_code, 200)
        posts = response.context.get('page_obj')
        self.assertIn(
            self.post,
            posts,
        )
        response_second_user = self.second_test_user.get(
            reverse('posts:follow_index'),
        )
        second_posts = response_second_user.context.get('page_obj')
        self.assertNotIn(
            self.post,
            second_posts,
        )
