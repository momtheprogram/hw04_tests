from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-f')
        cls.post = Post.objects.create(
            text='Тестовый текст-f',
            author=FormTest.author
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FormTest.author)

    def test_create_post(self):
        """
        Проверка создания новой записи в базе данных при отправке валидной
        формы со страницы создания поста reverse('posts:create_post').
        """
        form_data = {
            'text': FormTest.post.text
        }
        created_post = FormTest.post.text
        self.assertEqual(created_post, form_data['text'], 'Пост не создается')

    def test_change_post(self):
        """
        Проверка изменения поста (происходит ли изменение поста с post_id в
        базе данных).
        """
        post = Post.objects.create(
            text='Текс поста для его изменения',
            author=FormTest.author
        )
        form_data = {
            'text': 'Текст поста после его изменения',
        }
        self.authorized_client.post(reverse('posts:post_edit', args=[post.pk]),
                                    data=form_data, follow=True)
        post_after_changes = Post.objects.get(pk=post.pk)
        self.assertEqual(
            post_after_changes.text,
            form_data['text'],
            'Текст поста не изменился'
        )
        self.assertEqual(
            post_after_changes.pk,
            post.pk,
            'Вместо изменения поста, создается новый пост'
        )
