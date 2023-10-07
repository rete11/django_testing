from typing import List, Tuple

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note


User = get_user_model()


class TestNoteList(TestCase):
    """
    Класс для тестирования ситуаци, в которой
    отдельная заметка передаётся на страницу со списком заметок
    в списке object_list в словаре context;
    """

    # Константа адреса списка заметок
    List_URL = reverse("notes:list")

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
        response = self.client.get(self.List_URL)
        object_list = response.context["object_list"]
        self.assertIn(self.notes, object_list)


class TestOtherUsersNotes(TestCase):
    """
    Класс для тестирования ситуации, в которой в список заметок одного
    пользователя не попадают заметки другого пользователя
    """

    # Константа адреса списка заметок
    List_URL = reverse("notes:list")

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Создание тестовых данных, нужных для всех тестов этого класса.
        """
        cls.user1: User = User.objects.create(username="user1")
        cls.user2: User = User.objects.create(username="user2")

        # Константы для генерации списка заметок
        NUM_NOTE1: int = 5
        NUM_NOTE2: int = 10

        notes1: List[Note] = [
            Note(
                title=f"Заголовок {index}",
                text="Текст{index}",
                author=cls.user1,
                slug=index,
            )
            for index in range(NUM_NOTE1)
        ]
        Note.objects.bulk_create(notes1)
        notes2: List[Note] = [
            Note(
                title=f"Заголовок {index}",
                text="Текст{index}",
                author=cls.user2,
                slug=index,
            )
            for index in range(NUM_NOTE1, NUM_NOTE2)
        ]
        Note.objects.bulk_create(notes2)

    def test_user_notes_list(self) -> None:
        """
        Проверка на вхождение записей в списки пользователей.
        """
        self.client.force_login(self.user1)
        response = self.client.get(self.List_URL)
        user1_notes = Note.objects.filter(author=self.user1)
        user2_notes = Note.objects.filter(author=self.user2)
        for note in user1_notes:
            self.assertContains(response, note.title)
        for note in user2_notes:
            self.assertNotContains(response, note.title)
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(self.List_URL)
        for note in user2_notes:
            self.assertContains(response, note.title)
        for note in user1_notes:
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
        urls: Tuple[str, int or None] = (("notes:edit", (self.notes.slug,)),
                                         ("notes:add", None))
        self.client.force_login(self.user)
        for name, args in urls:
            with self.subTest(user=self.user, name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn("form", response.context)
