from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """
    Класс для тестового кейса, проверяющий доступность страниц сайта.
    """
    @classmethod
    def setUpTestData(cls) -> None:
        """Метод создает необходимые данные для тестирования."""
        cls.author: User = User.objects.create(username="Иван Кулибин")
        cls.reader: User = User.objects.create(username="Пользователь")
        cls.notes: Note = Note.objects.create(
            title="Заголовок", text="Текст", author=cls.author
        )

    def test_pages_availability(self) -> None:
        """
        Тестирует доступность основных страниц сайта.
        Главная страница доступна анонимному пользователю.
        Страницы регистрации пользователей, входа в
        учётную запись и выхода из неё доступны всем
        не зарегистрированным пользователям
        """
        urls = (
            ("notes:home", None),
            ("users:login", None),
            ("users:logout", None),
            ("users:signup", None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_user_for_notes_done_and_add(self) -> None:
        """Тестирует доступность страниц для авторизованных пользователей."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.OK),
        )

        urls = (
            ("notes:add", None),
            ("notes:success", None),
            ("notes:list", None),
            ("users:login", None),
            ("users:logout", None),
            ("users:signup", None),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name, args in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_note_author(self) -> None:
        """
        Тестирует доступность страниц редактирования, просмотра и удаления
        записей для разных пользователей.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ("notes:edit", (self.notes.slug,)),
            ("notes:detail", (self.notes.slug,)),
            ("notes:delete", (self.notes.slug,)),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name, args in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self) -> None:
        """
        Тестирует редирект на страницу логина для неавторизованных
        пользователей.
        """
        # Сохраняем адрес страницы логина:
        login_url = reverse("users:login")
        urls = (
            ("notes:add", None),
            ("notes:success", None),
            ("notes:list", None),
            ("notes:edit", (self.notes.slug,)),
            ("notes:detail", (self.notes.slug,)),
            ("notes:delete", (self.notes.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f"{login_url}?next={url}"
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
