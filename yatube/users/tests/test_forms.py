from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class PostFormTests(TestCase):
    def setUp(self):
        self.username = 'user'
        self.password = 'HUjnsdefdseDFdsgjkoolj2jDdfdeuskPn1dj'

    def test_signup(self):
        """Проверка возможности зарегистрироваться по валидной форме."""
        form_data = {
            'username': self.username,
            'first_name': 'aaa',
            'last_name': 'bbb',
            'email': 'aaa@ya.ru',
            'password1': self.password,
            'password2': self.password,
        }
        self.client.post(reverse(
            'users:signup'),
            data=form_data,
        )
        users = get_user_model().objects.all()
        self.assertEqual(users.count(), 1)
