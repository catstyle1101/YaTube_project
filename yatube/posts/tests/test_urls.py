from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.second_user = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.second_authorised_client = Client()
        self.second_authorised_client.force_login(self.second_user)

    def test_urls_exists_and_uses_correct_template(self):
        """Проверка шаблонов urls приложения posts."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/post_detail.html': '/posts/1/',
            'posts/profile.html': '/profile/auth/',
        }
        for template, address in templates_url_names.items():
            response = self.guest_client.get(address)
            self.assertTemplateUsed(
                response,
                template,
                f'template {template} not using on address {address}'
            )
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f'test url {address} failed'
            )

    def test_unexisting_page_returns_404(self):
        """Проверка, что не существующая страница выдает ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_post_unauthorized_user(self):
        """Проверка, что страница /create/ недоступна не авторизованному
        пользователю и она перенаправляет его на страницу /auth/login/."""
        url = '/create/'
        response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_create_post_authorized_user(self):
        """Проверка, что страница /create/ доступна авторизованному
        пользователю."""
        url = '/create/'
        response = self.authorised_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_post_authorized_user(self):
        """Проверка, что авторизованный пользователь может
        редактировать свой Post."""
        url = '/posts/1/edit/'
        response = self.authorised_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_post_not_autor(self):
        """Проверка, что авторизованный пользователь не может редактировать
        чужой Post."""
        url = '/posts/1/edit/'
        response = self.second_authorised_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_edit_post_unathorised(self):
        """Проверка, что неавторизованный пользователь не может редактировать
        Post."""
        url = '/posts/1/edit/'
        response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')
