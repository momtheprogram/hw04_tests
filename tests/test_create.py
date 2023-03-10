import pytest
from django import forms
from posts.models import Post


class TestCreateView:

    @pytest.mark.django_db(transaction=True)
    def test_create_view_get(self, user_client):
        try:
            response = user_client.get('/create/')
        except Exception as e:
            assert False, f'''Страница `/create/` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = user_client.get('/create/')
        assert response.status_code != 404, 'Страница `/create/` не найдена, проверьте этот адрес в *urls.py*'
        assert 'form' in response.context, 'Проверьте, что передали форму `form` в контекст страницы `/create/`'
        assert len(response.context['form'].fields) == 2, 'Проверьте, что в форме `form` на страницу `/create/` 2 поля'
        assert 'group' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/create/` есть поле `group`'
        )
        assert type(response.context['form'].fields['group']) == forms.models.ModelChoiceField, (
            'Проверьте, что в форме `form` на странице `/create/` поле `group` типа `ModelChoiceField`'
        )
        assert not response.context['form'].fields['group'].required, (
            'Проверьте, что в форме `form` на странице `/create/` поле `group` не обязательно'
        )

        assert 'text' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/create/` есть поле `text`'
        )
        assert type(response.context['form'].fields['text']) == forms.fields.CharField, (
            'Проверьте, что в форме `form` на странице `/create/` поле `text` типа `CharField`'
        )
        assert response.context['form'].fields['text'].required, (
            'Проверьте, что в форме `form` на странице `/create/` поле `text` обязательно'
        )

    @pytest.mark.django_db(transaction=True)
    def test_create_view_post(self, user_client, user, group):
        text = 'Проверка нового поста!'
        try:
            response = user_client.get('/create')
        except Exception as e:
            assert False, f'''Страница `/create` работает неправильно. Ошибка: `{e}`'''
        url = '/create/' if response.status_code in (301, 302) else '/create'

        response = user_client.post(url, data={'text': text, 'group': group.id})

        assert response.status_code in (301, 302), (
            'Проверьте, что со страницы `/create/` после создания поста, '
            f'перенаправляете на страницу профиля автора `/profile/{user.username}`'
        )
        post = Post.objects.filter(author=user, text=text, group=group).first()
        assert post is not None, 'Проверьте, что вы сохранили новый пост при отправки формы на странице `/create/`'
        assert response.url == f'/profile/{user.username}/', (
            f'Проверьте, что перенаправляете на страницу профиля автора `/profile/{user.username}`'
        )

        text = 'Проверка нового поста 2!'
        response = user_client.post(url, data={'text': text})
        assert response.status_code in (301, 302), (
            'Проверьте, что со страницы `/create/` после создания поста, '
            f'перенаправляете на страницу профиля автора `/profile/{user.username}`'
        )
        post = Post.objects.filter(author=user, text=text, group__isnull=True).first()
        assert post is not None, 'Проверьте, что вы сохранили новый пост при отправке формы на странице `/create/`'
        assert response.url == f'/profile/{user.username}/', (
            f'Проверьте, что перенаправляете на страницу профиля автора `/profile/{user.username}`'
        )

        response = user_client.post(url)
        assert response.status_code == 200, (
            'Проверьте, что на странице `/create/` выводите ошибки при неправильной заполненной формы `form`'
        )
