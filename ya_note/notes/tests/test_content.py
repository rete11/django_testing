from typing import List, Tuple

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

from notes.models import Note


User = get_user_model()


class TestNoteList(TestCase):
    """
    Класс для тестирования ситуаци, в которой
    отдельная заметка передаётся на страницу со списком заметок
    в списке object_list в словаре context;
    """

    # Константа адреса списка заметок
    LIST_URL = reverse("notes:list")

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Создание тестовых данных, нужных для всех тестов этого класса.
        """
        cls.author: User = User.objects.create(username="Иван Кулибин")
        cls.notes: Note = Note.objects.create(
            title="Заголовок", text="Текст", author=cls.author
        )

    def test_note_in(self) -> None:
        """
        Проверка на наличие заметок автора в ответе на запрос.
        """
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context["object_list"]
        self.assertIn(self.notes, object_list)


class TestOtherUsersNotes(TestCase):
    """
    Класс для тестирования ситуации, в которой в список заметок одного
    пользователя не попадают заметки другого пользователя
    """

    # Константа адреса списка заметок
    LIST_URL = reverse("notes:list")

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Создание тестовых данных, нужных для всех тестов этого класса.
        """
        cls.author: User = User.objects.create(username="Автор")
        cls.reader: User = User.objects.create(username="Читатель")
        notes_author: List[Note] = [
            Note(
                title=f"Заголовок {index}",
                text="Текст{index}",
                author=cls.author,
                slug=index,
            )
            for index in range(settings.NUM_NOTE1)
        ]
        Note.objects.bulk_create(notes_author)
        notes_reader: List[Note] = [
            Note(
                title=f"Заголовок {index}",
                text="Текст{index}",
                author=cls.reader,
                slug=index,
            )
            for index in range(settings.NUM_NOTE1, settings.NUM_NOTE2)
        ]
        Note.objects.bulk_create(notes_reader)

    def test_user_notes_list(self) -> None:
        """
        Проверка на вхождение записей в списки пользователей.
        """
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        author_notes = Note.objects.filter(author=self.author)
        reader_notes = Note.objects.filter(author=self.reader)
        for note in author_notes:
            self.assertContains(response, note.title)
        for note in reader_notes:
            self.assertNotContains(response, note.title)
        self.client.logout()
        self.client.force_login(self.reader)
        response = self.client.get(self.LIST_URL)
        for note in reader_notes:
            self.assertContains(response, note.title)
        for note in author_notes:
            self.assertNotContains(response, note.title)


class TestFormNotes(TestCase):
    """
    Класс для тестирования передачи форм
    на страницы создания и редактирования заметки.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Создание тестовых данных, нужных для всех тестов этого класса.
        """
        cls.user: User = User.objects.create(username="user1")
        cls.notes: Note = Note.objects.create(
            title="Заголовок", text="Текст", author=cls.user
        )

    def test_form_notes(self) -> None:
        """
        Проверка на включение формы в контекст при переходе
        на страницу добавления или редактирования записи.
        """
        urls: Tuple[str, int or None] = (
            ("notes:edit", (self.notes.slug,)),
            ("notes:add", None),
        )
        self.client.force_login(self.user)
        for name, args in urls:
            with self.subTest(user=self.user, name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn("form", response.context)
