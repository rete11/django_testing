from http import HTTPStatus
from functools import wraps

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreationAndNoteDuplicateSlug(TestCase):
    """
    Класс тестовых случаев создания записей.
    Проверяет Залогиненный пользователь может создать заметку,
    а анонимный — не может. Также применяется для проверки
    создания заметок с одинаковым слагом.
    """

    # Константа текста заметки
    NOTE_TEXT: str = "Текст заметки"
    # Константа заголовка заметки
    NOTE_TITLE: str = "Заголовок заметки"

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Метод настраивает исходные данные для тестов.
        Создает пользователя и определяет начальные данные формы
        и URL для создания заметки.
        """
        cls.user: User = User.objects.create(username="Автор")
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.notes: Note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug="happy",
            author=cls.user,
        )
        cls.form_data: dict = {"title": cls.NOTE_TITLE, "text": cls.NOTE_TEXT}
        cls.url: str = reverse("notes:add")

    def test_duplicate_slug_creation_fails2(self) -> None:
        """
        Тестирование невозможности создания записи с дублирующим слагом.
        Пытаемся создать запись с тем же слагом, который уже был использован.
        Проверяем, что вызывается исключение ValidationError.
        """
        duplicate_note: Note = Note(
            title="Новый заголовок",
            text="Новый текст заметки",
            slug="happy",
            author=self.user,
        )
        with self.assertRaises(ValidationError):
            duplicate_note.full_clean()
            duplicate_note.save()

    def test_authenticated_user_can_create_a_note(self) -> None:
        """
        Метод проверяет, что залогиненный пользователь при создании заметки
        через POST-запрос перенаправляется на страницу успешного создания
        заметки, и количество заметок увеличивается на 1.
        """
        self.client.force_login(self.user)
        initial_notes_count: int = Note.objects.count()
        response: Client = self.client.post(self.url, data=self.form_data)
        notes_count_after_post: int = Note.objects.count()
        self.assertRedirects(
            response,
            expected_url=reverse("notes:success"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
        self.assertEqual(notes_count_after_post, initial_notes_count + 1)

    def test_anonymous_user_cannot_create_a_note(self) -> None:
        """
        Проверяет, что анонимный пользователь не может создать заметку.

        """
        initial_notes_count: int = Note.objects.count()
        response: Client = self.client.post(self.url, self.form_data)
        notes_count_after_post: int = Note.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(initial_notes_count, notes_count_after_post)


class TestNoteEditDeleteAndNoteNoneSlug(TestCase):
    """
    Класс тестового сценария для проверки операций редактирования и удаления
    заметок в приложении примечаний.
    Проверяет, что пользователь может редактировать и удалять свои заметки,
    но не может редактировать или удалять чужие, а также
    для испытания сценариев создания записей без слага (slug).
    """

    # Константа текста заметки
    NOTE_TEXT: str = "Текст заметки"
    # Константа заголовка заметки
    NOTE_TITLE: str = "Заголовок"

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Дед")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader: User = User.objects.create(username="Пользователь")
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём объект заметки.
        cls.notes: Note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT, author=cls.author
        )
        # Список URL для действий с заметками.
        cls.edit_url = reverse("notes:edit", args=(cls.notes.slug,))
        cls.delete_url = reverse("notes:delete", args=(cls.notes.slug,))
        cls.success_url = reverse("notes:success")
        # Формируем данные для POST-запроса по обновлению заметки.
        cls.form_data = {"title": cls.NOTE_TITLE, "text": cls.NOTE_TEXT}

    def test_slug_creation_if_none_provided2(self) -> None:
        """
        Проверяет, что если слаг не был указан при создании записи,
        то слаг автоматически создается с помощью функции
        pytils.translit.slugify.
        """
        self.assertIsNotNone(self.notes.slug)
        self.assertEqual(self.notes.slug, slugify(self.notes.title)[:100])

    def test_author_can_delete_note(self) -> None:
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        self.assertRedirects(
            self.author_client.delete(self.delete_url), self.success_url
        )
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self) -> None:
        # Выполняем запрос на удаление от пользователя - не автора заметки.
        self.assertEqual(
            self.reader_client.delete(self.delete_url).status_code,
            HTTPStatus.NOT_FOUND,
        )
        self.assertEqual(Note.objects.count(), 1)

    def refresh_and_check(f):
        """
        Декоратор, выполняющий операцию обновления объекта заметки
        и проверяющий, что текст и заголовок не изменились.
        """

        @wraps(f)
        def decorated(*args, **kwargs):
            # Вызываем оригинальную функцию
            original_result = f(*args, **kwargs)
            self = args[0]
            self.notes.refresh_from_db()
            # Проверяем, что текст и заголовок заметки остались теми же
            self.assertEqual(self.notes.title, self.NOTE_TITLE)
            self.assertEqual(self.notes.text, self.NOTE_TEXT)
            # Возвращаем результат функции
            return original_result

        return decorated

    @refresh_and_check
    def test_author_can_edit_note(self) -> None:
        # Выполняем запрос на редактирование от имени автора заметки.
        self.assertRedirects(
            self.author_client.post(self.edit_url, data=self.form_data),
            self.success_url,
        )

    @refresh_and_check
    def test_user_cant_edit_note_of_another_user(self) -> None:
        # Выполняем запрос на редактирование от имени другого пользователя.
        self.assertEqual(
            self.reader_client.post(
                self.edit_url, data=self.form_data
            ).status_code,
            HTTPStatus.NOT_FOUND,
        )
