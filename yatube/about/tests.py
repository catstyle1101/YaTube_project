from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus


class AboutTestURL(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_about(self):
        """Проверка шаблонов и доступности about."""
        urls = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Test {url} failed',
                )
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Template {template} not using on address {url}',
                )


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """Проверка, что страница about доступна."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        """Проверка шаблонов about."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertTemplateUsed(response, 'about/author.html')

    def test_tech_page_accessible_by_name(self):
        """Проверка доступности tech."""
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        """Проверка шаблона tech."""
        response = self.guest_client.get(reverse('about:tech'))
        self.assertTemplateUsed(response, 'about/tech.html')
