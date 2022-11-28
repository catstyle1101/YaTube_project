from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from http import HTTPStatus

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)

    def test_url_authorised_users(self):
        """Проверка доступности urls приложения users."""
        templates_urls = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/<uibd64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/logout/': 'users/logged_out.html',
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.authorised_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
            with self.subTest(url=url):
                response = self.authorised_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Template {template} on url {url} is not found'
                )

    def test_url_unauthorised_users(self):
        """Проверка доступности страниц приложение users для
        неавторизованного пользователя."""
        templates_urls = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/<uibd64>/<token>/':
                'users/password_reset_confirm.html',
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Template {template} on url {url} is not found'
                )
