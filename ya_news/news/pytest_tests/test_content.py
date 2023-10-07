from typing import Any

import pytest
from django.urls import reverse
from django.conf import settings


@pytest.mark.django_db
def test_news_list_show_max_10_news(client: Any, create_news: Any) -> None:
    """
    Тест проверяет, что на главной странице отображается не более 10 новостей.
    """
    url: str = reverse("news:home")
    response = client.get(url)
    news_list = response.context["object_list"]
    assert len(news_list) <= settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_list_order(client: Any, create_news: Any) -> None:
    """
    Тест проверяет, порядок новостей на главной странице.
    Свежие новости в начале списка.
    """
    url: str = reverse("news:home")
    response = client.get(url)
    news_list = response.context["object_list"]
    all_dates = [news.date for news in news_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client: Any, news: Any, create_comments: Any) -> None:
    url: str = reverse("news:detail", args=(news.pk,))
    response = client.get(url)
    news = response.context["news"]
    comments: list = list(
        response.context["news"].comment_set.all().order_by("created")
    )
    assert len(comments) >= 2
    assert comments[0].created < comments[1].created


@pytest.mark.parametrize(
    "parametrize_client, form_in_context",
    (
        (pytest.lazy_fixture("client"), False),
        (pytest.lazy_fixture("admin_client"), True),
    ),
)
@pytest.mark.django_db
def test_anonym_auth_user_contains_form(
    parametrize_client: Any, form_in_context: bool, news: Any
) -> None:
    """
    Тест проверяет, что анонимному пользователю недоступна форма
    для отправки комментария на странице отдельной новости, а авторизованному
    пользователю - доступна.
    """
    url = reverse("news:detail", args=(news.pk,))
    response = parametrize_client.get(url)
    assert ("form" in response.context) is form_in_context
