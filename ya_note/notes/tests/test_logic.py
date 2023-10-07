# from typing import Any
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    """
    Класс тестовых случаев создания записей.
    Проверяет Залогиненный пользователь может создать заметку,
    а анонимный — не может.
    """

    # Константа текста заметки
    NOTE_TEXT: str = "И от тебя уйду"
    # Константа заголовка заметки
    NOTE_TITLE: str = "Ответ голодным животным"

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Метод настраивает исходные данные для тестов.
        Создает пользователя и определяет начальные данные формы
        и URL для создания заметки.
        """
        cls.user: User = User.objects.create(
            username="Колобок Дедушкин-Бабковский"
        )
        cls.form_data: dict = {"title": cls.NOTE_TITLE, "text": cls.NOTE_TEXT}
        cls.url: str = reverse("notes:add")

    def test_authenticated_user_can_create_a_note(self) -> None:
        """
        Метод проверяет, что залогиненный пользователь при создании заметки
        через POST-запрос перенаправляется на страницу успешного создания
        заметки, и количество заметок увеличивается на 1.
        """
        succes_url: str = reverse("notes:success")
        self.client.force_login(self.user)
        initial_notes_count: int = Note.objects.count()
        response: Client = self.client.post(self.url, data=self.form_data)
        notes_count_after_post: int = Note.objects.count()
        self.assertRedirects(
            response,
            expected_url=succes_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
        self.assertEqual(notes_count_after_post, initial_notes_count + 1)
        response = self.client.post(self.url, self.form_data)

    def test_anonymous_user_cannot_create_a_note(self) -> None:
        """
        Проверяет, что анонимный пользователь не может создать заметку.

        Этот метод проверяет, что анонимный пользователь при попытке создания
        заметки через POST-запрос перенаправляется на страницу логина и
        количество заметок не изменяется.
        """
        initial_notes_count: int = Note.objects.count()
        response: Client = self.client.post(self.url, self.form_data)
        notes_count_after_post: int = Note.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(initial_notes_count, notes_count_after_post)


class TestNoteDuplicateSlug(TestCase):
    """
    Класс тестовых случаев для проверки создания заметок с одинаковым слагом.

    Создаем тестового пользователя и запись. Пытаемся создать другую запись
    с тем же слагом. Проверяем, что будет вызвано исключение ValidationError.
    """

    # Константа текста заметки
    NOTE_TEXT: str = "И от тебя уйду"
    # Константа заголовка заметки
    NOTE_TITLE: str = "Ответ голодным животным"

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Установка начальных данных для тестов.

        Создаем пользователя, запись и клиента авторизации.
        """
        cls.user: User = User.objects.create(
            username="Колобок Дедушкин-Бабковский"
        )
        cls.notes: Note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug="happy",
            author=cls.user,
        )
        cls.auth_client: Client = Client()
        cls.auth_client.force_login(cls.user)

        cls.form_data: dict = {"title": cls.NOTE_TITLE, "text": cls.NOTE_TEXT}
        cls.url: str = reverse("notes:add")

    def test_duplicate_slug_creation_fails(self) -> None:
        """
        Тестирование невозможности создания записи с дублирующим слагом.

        Пытаемся создать запись с тем же слагом, который уже был использован.
        Проверяем, что вызывается исключение ValidationError.
        """
        self.client.force_login(self.user)
        duplicate_note: Note = Note(
            title="Не ешь меня",
            text="Я тебе песенку спою",
            slug="happy",
            author=self.user,
        )
        with self.assertRaises(ValidationError):
            duplicate_note.full_clean()
            duplicate_note.save()


class TestNoteNoneSlug(TestCase):
    """
    Класс для испытания сценариев создания записей без слага (slug).
    Если слаг не указан при создании записи, проверяем, что он создается
    автоматически.
    """

    # Константа текста заметки
    NOTE_TEXT: str = "И от тебя уйду"
    # Константа заголовка заметки
    NOTE_TITLE: str = "Ответ голодным животным"

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Инициализирует тестовые данные: создает пользователя и запись от его
        имени, затем авторизует пользователя для дальнейших тестов.
        """
        cls.user: User = User.objects.create(
            username="Колобок Дедушкин-Бабковский"
        )
        cls.notes: Note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT, author=cls.user
        )
        cls.auth_client: Client = Client()
        cls.auth_client.force_login(cls.user)

    def test_slug_creation_if_none_provided(self) -> None:
        """
        Проверяет, что если слаг не был указан при создании записи,
        то слаг автоматически создается с помощью функции
        pytils.translit.slugify.
        """
        self.client.force_login(self.user)
        note = self.notes
        self.assertIsNotNone(note.slug)
        self.assertEqual(note.slug, slugify(note.title)[:100])


class TestNoteEditDelete(TestCase):
    """
    Класс тестового сценария для проверки операций редактирования и удаления
    заметок в приложении примечаний.
    Проверяет, что пользователь может редактировать и удалять свои заметки,
    но не может редактировать или удалять чужие.
    """

    # Константа текста заметки
    NOTE_TEXT: str = "И от тебя уйду"
    # Константа заголовка заметки
    NOTE_TITLE: str = "Ответ голодным животным"

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            username="Колобок Дедушкин-Бабковский"
        )
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя- не автора заметки.
        cls.reader: User = User.objects.create(username="Пользователь")
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём объект заметки.
        cls.notes: Note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT, author=cls.author
        )
        cls.url_to_note = reverse("notes:detail", args=(cls.notes.slug,))
        # URL для редактирования заметки.
        cls.edit_url = reverse("notes:edit", args=(cls.notes.slug,))
        # URL для удаления заметки.
        cls.delete_url = reverse("notes:delete", args=(cls.notes.slug,))
        cls.success_url = reverse("notes:success")
        # Формируем данные для POST-запроса по обновлению заметки.
        cls.form_data = {"title": cls.NOTE_TITLE, "text": cls.NOTE_TEXT}

    def test_author_can_delete_note(self) -> None:
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с заметкой.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.success_url)
        # Считаем количество заметок в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль заметок в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self) -> None:
        # Выполняем запрос на удаление от пользователя - не автора заметки.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self) -> None:
        # Выполняем запрос на редактирование от имени автора заметки.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.success_url)
        # Обновляем объект заметки.
        self.notes.refresh_from_db()
        # Проверяем, что текст заметки соответствует обновленному.
        self.assertEqual(self.notes.title, self.NOTE_TITLE)
        self.assertEqual(self.notes.text, self.NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self) -> None:
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект заметки.
        self.notes.refresh_from_db()
        # Проверяем, что текст и заголовок остался тем же, что и был.
        self.assertEqual(self.notes.title, self.NOTE_TITLE)
        self.assertEqual(self.notes.text, self.NOTE_TEXT)
