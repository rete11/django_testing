from typing import Any
from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects
from django.urls import reverse


@pytest.mark.parametrize(
    # Значения, которые будут передаваться в name и args.
    "name, args",
    (
        ("news:detail", pytest.lazy_fixture("slug_for_args")),
        ("news:home", None),
        ("users:login", None),
        ("users:logout", None),
        ("users:signup", None),
    ),
)
@pytest.mark.django_db
def test_pages_availability_for_anonymous_user(
    client: Any, name: str, args: Any
) -> None:
    """
    Тест проверяет:
    - главная страница доступна анонимному пользователю;
    - страница отдельной новости доступна анонимному пользователю;
    - страницы регистрации пользователей, входа в учётную запись и
    выхода из неё доступны анонимным пользователям.
    """
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    # Значения, которые будут передаваться в name и args.
    "name, args",
    (
        ("news:edit", pytest.lazy_fixture("slug_for_args")),
        ("news:delete", pytest.lazy_fixture("slug_for_args")),
    ),
)
@pytest.mark.django_db
def test_coment_edit_delete_for_auth_users(
    admin_client: Any, name: str, args: Any
) -> None:
    """
    Тест проверяет, что авторизованный пользователь не может зайти
    на страницы редактирования или удаления чужих комментариев
    (возвращается ошибка 404).
    """
    url = reverse(name, args=args)
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "name",
    ("news:edit", "news:delete"),
)
def test_coment_edit_delete_for__author(
    author_client: Any, name: str, comment: Any
) -> None:
    """
    Тест проверяет, что страницы удаления и редактирования комментария доступны
    автору комментария.
    """
    url = reverse(name, args=(comment.id,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "name, args",
    (
        ("news:edit", pytest.lazy_fixture("slug_for_args")),
        ("news:delete", pytest.lazy_fixture("slug_for_args")),
    ),
)
@pytest.mark.django_db
def test_redirects(client: Any, name: str, args: Any) -> None:
    """
    Тест проверяет, что при попытке перейти на страницу
    редактирования или удаления комментария анонимный
    пользователь перенаправляется на страницу авторизации.
    """
    login_url = reverse("users:login")
    url = reverse(name, args=args)
    expected_url = f"{login_url}?next={url}"
    response = client.get(url)
    assertRedirects(response, expected_url)
