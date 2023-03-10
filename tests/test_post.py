import pytest
from django import forms
from posts.forms import PostForm
from posts.models import Post

from tests.utils import get_field_from_context


class TestPostView:

    @pytest.mark.django_db(transaction=True)
    def test_post_view_get(self, client, post_with_group):
        try:
            response = client.get(f'/posts/{post_with_group.id}')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = client.get(f'/posts/{post_with_group.id}/')
        assert response.status_code != 404, (
            'Страница `/posts/<post_id>/` не найдена, проверьте этот адрес в *urls.py*'
        )

        post_context = get_field_from_context(response.context, Post)
        assert post_context is not None, (
            'Проверьте, что передали статью в контекст страницы `/posts/<post_id>/` типа `Post`'
        )


class TestPostEditView:

    @pytest.mark.django_db(transaction=True)
    def test_post_edit_view_get(self, client, post_with_group):
        try:
            response = client.get(f'/posts/{post_with_group.id}/edit')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/edit/` работает неправильно. Ошибка: `{e}`'''
        if (
                response.status_code in (301, 302)
                and not response.url.startswith(f'/posts/{post_with_group.id}')
        ):
            response = client.get(f'/posts/{post_with_group.id}/edit/')
        assert response.status_code != 404, (
            'Страница `/posts/<post_id>/edit/` не найдена, проверьте этот адрес в *urls.py*'
        )

        assert response.status_code in (301, 302), (
            'Проверьте, что вы переадресуете пользователя со страницы '
            '`/<username>/<post_id>/edit/` на страницу поста, если он не автор'
        )

    @pytest.mark.django_db(transaction=True)
    def test_post_edit_view_author_get(self, user_client, post_with_group):
        try:
            response = user_client.get(f'/posts/{post_with_group.id}/edit')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/edit/` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = user_client.get(f'/posts/{post_with_group.id}/edit/')
        assert response.status_code != 404, (
            'Страница `/posts/<post_id>/edit/` не найдена, проверьте этот адрес в *urls.py*'
        )

        post_context = get_field_from_context(response.context, Post)
        postform_context = get_field_from_context(response.context, PostForm)
        assert any([post_context, postform_context]) is not None, (
            'Проверьте, что передали статью в контекст страницы `/posts/<post_id>/edit/` типа `Post` или `PostForm`'
        )

        assert 'form' in response.context, (
            'Проверьте, что передали форму `form` в контекст страницы `/posts/<post_id>/edit/`'
        )
        assert len(response.context['form'].fields) == 2, (
            'Проверьте, что в форме `form` на страницу `/posts/<post_id>/edit/` 2 поля'
        )
        assert 'group' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` есть поле `group`'
        )
        assert type(response.context['form'].fields['group']) == forms.models.ModelChoiceField, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `group` типа `ModelChoiceField`'
        )
        assert not response.context['form'].fields['group'].required, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `group` не обязательно'
        )

        assert 'text' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` есть поле `text`'
        )
        assert type(response.context['form'].fields['text']) == forms.fields.CharField, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `text` типа `CharField`'
        )
        assert response.context['form'].fields['text'].required, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `group` обязательно'
        )

    @pytest.mark.django_db(transaction=True)
    def test_post_edit_view_author_post(self, user_client, post_with_group):
        text = 'Проверка изменения поста!'
        try:
            response = user_client.get(f'/posts/{post_with_group.id}/edit')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/edit/` работает неправильно. Ошибка: `{e}`'''
        url = (
            f'/posts/{post_with_group.id}/edit/'
            if response.status_code in (301, 302)
            else f'/posts/{post_with_group.id}/edit'
        )

        response = user_client.post(url, data={'text': text, 'group': post_with_group.group_id})

        assert response.status_code in (301, 302), (
            'Проверьте, что со страницы `/posts/<post_id>/edit/` '
            'после создания поста перенаправляете на страницу поста'
        )
        post = Post.objects.filter(author=post_with_group.author, text=text, group=post_with_group.group).first()
        assert post is not None, (
            'Проверьте, что вы изменили пост при отправки формы на странице `/posts/<post_id>/edit/`'
        )
        assert response.url.startswith(f'/posts/{post_with_group.id}'), (
            'Проверьте, что перенаправляете на страницу поста `/posts/<post_id>/`'
        )
