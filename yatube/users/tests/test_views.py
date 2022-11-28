from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

User = get_user_model()


class UsersPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_page_uses_correct_template(self):
        """Проверка, что страница login использует верный шаблон."""
        templates_pages_names = {
            reverse('users:login'): 'users/login.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_page_context(self):
        """Проверка словаря context страницы login."""
        form_fields = {
            'first_name': forms.CharField,
            'last_name': forms.CharField,
            'username': UsernameField,
            'email': forms.EmailField,
            'password1': forms.CharField,
            'password2': forms.CharField,
        }
        response = self.guest_client.get(reverse('users:signup'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
