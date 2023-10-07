from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertFormError


from news.forms import WARNING, BAD_WORDS
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, form_data, news):
    """
    Тест проверяет, что анонимный пользователь не может отправить комментарий.
    """
    url = reverse("news:detail", args=(news.pk,))
    response = client.post(url, data=form_data)
    login_url = reverse("users:login")
    expected_url = f"{login_url}?next={url}"
    assertRedirects(response, expected_url)
    assert not Comment.objects.exists()


def test_user_can_create_comment(author_client, form_data, news):
    """
    Тест проверяет, что авторизованный пользователь может отправить
    комментарий.
    """
    url = reverse("news:detail", args=(news.pk,))
    response = author_client.post(url, data=form_data)
    assertRedirects(response, reverse(
        "news:detail", args=(news.pk,)) + '#comments'
    )
    assert Comment.objects.count() == 1
    new_сomment = Comment.objects.get()
    assert new_сomment.text == form_data["text"]


def test_user_cant_use_bad_words(admin_client, form_data, news):
    """
    Тест проверяет, что Если комментарий содержит запрещённые
    слова, он не будет опубликован, а форма вернёт ошибку.
    """

    url = reverse("news:detail", args=(news.pk,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(author_client, form_data, comment):
    '''
    Тест проверяет, что авторизованный пользователь может
    редактировать или удалять свои комментарии.
    '''
    url = reverse("news:edit", args=(comment.id,))
    response = author_client.post(url, form_data)
    assertRedirects(response, reverse(
        "news:detail", args=(comment.id,)) + '#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_other_user_cant_edit_comment(admin_client, form_data, comment):
    '''
    Тест проверяет, что авторизованный пользователь
    не может редактировать  чужие комментарии.
    '''
    url = reverse("news:edit", args=(comment.id,))
    response = admin_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text


def test_author_can_delete_comment(author_client, slug_for_args):
    '''
    Тест проверяет, что авторизованный пользователь
    может  удалять свои комментарии.
    '''
    url = reverse('news:delete', args=slug_for_args)
    response = author_client.post(url)
    assertRedirects(response, reverse(
        "news:detail", args=slug_for_args) + '#comments'
    )
    assert Comment.objects.count() == 0


def test_other_user_cant_delete_comment(admin_client, slug_for_args):
    '''
    Тест проверяет, что авторизованный пользователь
    не может удалять чужие комментарии.
    '''
    url = reverse('news:delete', args=slug_for_args)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
