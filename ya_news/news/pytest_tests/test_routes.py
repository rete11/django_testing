import pytest
from http import HTTPStatus

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
def test_pages_availability_for_anonymous_user(client, name, args):
    url = reverse(name, args=args)  # Получаем ссылку на нужный адрес.
    response = client.get(url)  # Выполняем запрос.
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
def test_coment_edit_delete_for_auth_users(admin_client, name, args):
    url = reverse(name, args=args)
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "name",
    ("news:edit", "news:delete"),
)
def test_coment_edit_delete_for__author(author_client, name, comment):
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
def test_redirects(client, name, args):
    login_url = reverse("users:login")
    url = reverse(name, args=args)
    expected_url = f"{login_url}?next={url}"
    response = client.get(url)
    assertRedirects(response, expected_url)
