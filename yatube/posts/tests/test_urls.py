from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_username')
        cls.group = Group.objects.create(
            title='Test_title',
            slug='test_slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=PostURLTests.author,
            group=PostURLTests.group)

        group_slug = PostURLTests.group.slug
        username = PostURLTests.author.username
        post_id = PostURLTests.post.pk
        cls.url_templates_status_for_everybody = {
            '/': 'posts/index.html',
            f'/group/{group_slug}/': 'posts/group_list.html',
            f'/profile/{username}/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            }
        cls.url_templates_status_for_authorized = {
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self) -> None:
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.author)

    def test_urls_uses_correct_template(self):
        """
        Проверяем, что URL-адрес использует соответствующий
        шаблон (для всех пользователей).
        """
        for address, template in (PostURLTests.
                                  url_templates_status_for_everybody.
                                  items()
                                  ):
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    (f'По адресу {address} отображается неверный шаблон'
                     f' {template}')
                     )
                self.assertEqual(
                    response.status_code, 200
                )

    def test_urls_correct_template_for_authorized(self):
        """
        Проверяем, что URL-адрес использует соответствующий
        шаблон (для авторизованных пользователей).
        """
        for address, template in (PostURLTests.
                                  url_templates_status_for_authorized.
                                  items()
                                  ):
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'По адресу {address} отображается неверный шаблон {template}'
                    )
                self.assertEqual(response.status_code, 200)

    def test_for_authorized_not_author(self):
        """
        Проверка шаблона для авторизованного пользователя (не автора поста)
        """
        not_author = User.objects.create_user(username='test_authorized_user')
        not_author_authorized = Client()
        not_author_authorized.force_login(not_author)
        address = '/create/'
        template = 'posts/create_post.html'
        response = not_author_authorized.get(address)
        self.assertTemplateUsed(
            response,
            template,
            f'По адресу {address} отображается неверный шаблон {template}'
            )
        self.assertEqual(response.status_code, 200)

    def test_404_unexpected_page(self):
        address = 'unexpected_page'
        response = self.guest_client.get(address)
        self.assertEqual(response.status_code, 404)
