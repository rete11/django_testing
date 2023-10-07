from datetime import datetime, timedelta
from typing import Any

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def author(django_user_model) -> Any:
    """
    Фикстура, создающая автора в модели пользователей Django.

    Берет встроенную фикстуру модели пользователей Django.

    Возвращает экземпляр модели пользователя Django с установленным именем
    пользователя "Автор".
    """
    return django_user_model.objects.create(username="Автор")


@pytest.fixture
def author_client(author: Any, client: Any) -> Any:
    """
    Фикстура, логинящая автора в клиенте.

    Prerequisites: Фикстуры автора и клиента.

    Возвращает клиента с залогиненым автором.
    """
    client.force_login(author)
    return client


@pytest.fixture
def news() -> News:
    """
    Фикстура, создающая объект новости.
    Возвращает объект новости с заданным названием и текстом.
    """
    return News.objects.create(
        title="заголовок",
        text="Текст новости",
    )


@pytest.fixture
def slug_for_args(comment: Comment) -> tuple[int]:
    """
    Фикстура, возвращающая кортеж, содержащий ID комментария.

    Prerequisites: Фикстура создания комментария.

    Возвращает кортеж, который содержит ID комментария.
    """
    return (comment.id,)


@pytest.fixture
def comment(news: News, author: Any) -> Comment:
    """
    Фикстура, создающая объект комментария.

    Prerequisites: Фикстуры новости и автора.

    Возвращает объект комментария с заданной новостью, текстом и автором.
    """
    return Comment.objects.create(
        news=news, text="Текст комментария", author=author
    )


@pytest.fixture
def form_data() -> dict[str, str]:
    """
    Фикстура для формы.
    """
    return {
        "text": "Новый текст",
    }


@pytest.fixture
def create_news() -> None:
    """
    Фикстура для создания новостей.
    Создаёт пачку новостей с помощью bulk_create.
    Каждая новость имеет уникальный заголовок и текст,
    а также дата создания отстает на количество дней,
    соответствующее индексу новости.
    """
    today = datetime.today()
    return News.objects.bulk_create(
        News(
            title=f"Новость {index}",
            text="Просто текст.",
            date=today - timedelta(days=index),
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


@pytest.fixture
def create_comments(news: object) -> Comment:
    """
    Фиксированное значение для создания комментариев.
    Создаёт новые объекты Comment и записывает их в базу данных.
    Каждый комментарий имеет уникальный текст и дату и время создания.
    """
    NUM_COM: int = 2  # количество комментариев
    author = User.objects.create(username="Комментатор")
    # Создаём комментарии в цикле.
    for index in range(NUM_COM):
        # Создаём объект и записываем его в переменную.
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f"Tекст {index}",
        )
        comment.created = timezone.now() + timedelta(seconds=index)
        # И сохраняем эти изменения.
        comment.save()
    return comment
