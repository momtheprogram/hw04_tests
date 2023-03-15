from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from posts.models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user('author')
        cls.group = Group.objects.create(
            title='Title',
            slug='slug',
            description='description'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=PostPagesTests.author,
            group=PostPagesTests.group
        )

    def setUp(self) -> None:
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.author)

    def test_pages_uses_correct_template(self):
        args = {
            'kwargs': {'slug': self.group.slug},
            'author': {self.author},
            'id': {self.post.pk},
        }
        urls = {
            'group': 'posts/group_list.html',
            'profile': 'posts/profile.html',
            'detail': 'posts/post_detail.html',
            'create': 'posts/create_post.html',
        }
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs=args['kwargs']): urls['group'],
            reverse('posts:profile', args={self.author}): urls['profile'],
            reverse('posts:post_detail', args=args['id']): urls['detail'],
            reverse('posts:post_edit', args=args['id']): urls['create'],
            reverse('posts:post_create'): urls['create'],
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template,)

    def test_chek_context_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0].text
        self.assertEqual(first_obj, self.post.text)

    def test_chek_context_group_list(self):
        response = (self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        ))
        obj_post = response.context['page_obj'][0].group
        obj_group = response.context['group']
        self.assertEqual(
            obj_post.title,
            self.group.title,
            (f'Пост отсутствует на страничке "posts/group_list.html"'
             f' в группе {obj_group}'),
        )

    def test_chek_context_profile(self):
        another_post = Post.objects.create(
            text='Текст другого автора',
            author=self.author,
        )
        url = reverse('posts:profile', args=(self.author.username,))

        response = self.authorized_client.get(url)

        context_post = response.context['page_obj'][0]
        context_count = response.context['all_posts']
        context_author = response.context['author']
        self.assertEqual(context_post,
                         another_post,
                         'Некорректный контекст view "profile".'
                         )
        self.assertEqual(
            context_count,
            2,
            'В контексте profile некорректное число постов автора'
        )
        self.assertEqual(context_author, self.author)

    def test_chek_context_post_detail(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            args=[self.post.pk]
        ))
        context_post = response.context['post']
        context_count = response.context['post_count']
        self.assertEqual(
            context_post,
            self.post,
            'Неверный пост в контекте post_detail'
        )
        self.assertEqual(
            context_count,
            self.author.posts.count(),
            'Неверное количеств постов в контексте post_detail'
        )

    def test_chek_context_create_post_edit(self):
        post_form = PostForm(instance=self.post)
        url = reverse('posts:post_edit', args=[self.post.pk])
        response = self.authorized_client.get(url)

        context_form = response.context['form']
        context_is_edit = response.context['is_edit']
        context_post = response.context['post']

        self.assertIsInstance(context_form, type(post_form),)
        self.assertEqual(context_is_edit, True,)
        self.assertEqual(context_post, self.post,)
        self.assertEqual(context_form.instance, self.post,)

    def test_chek_context_create_post(self):
        form_type = type(PostForm())
        response = self.authorized_client.get(reverse('posts:post_create'))
        context_form = response.context['form']
        context_is_edit = response.context['is_edit']
        self.assertIsInstance(context_form, form_type,)
        self.assertEqual(context_is_edit, False,)

    def test_check_post_in_pages_group(self):
        """
        Появление поста на главной странице, странице выбранной группы,
        в профайле пользователя, если при создании поста указать группу.
        """
        url_2 = reverse('posts:group_list', kwargs={'slug': self.group.slug})
        url_3 = reverse('posts:profile', args=(self.author.username,))
        response1 = self.authorized_client.get(reverse('posts:index'))
        response2 = self.authorized_client.get(url_2)
        response3 = self.authorized_client.get(url_3)

        context1 = response1.context['page_obj'][0]
        context2 = response2.context['page_obj'][0].group.title
        context3 = response3.context['page_obj'][0]

        self.assertEqual(
            context1,
            self.post,
            'На главной странице нет созданного с группой поста'
        )
        self.assertEqual(
            context2,
            self.post.group.title,
            f'В группе {self.group.title} нет созданного поста'
        )
        self.assertEqual(
            context3,
            self.post,
            (f'В профайле пользователя {self.author.username}'
             f' нет созданного поста')
        )

    def test_post_not_in_an_outsider_group(self):
        """
        Отсутствие поста в группе, для которой он не был предназначен.
        """
        group = Group.objects.create(
            title='Simple_title',
            slug='simple-slug',
            description='simple_description'
        )
        url = reverse('posts:group_list', kwargs={'slug': self.group.slug})
        response = self.authorized_client.get(url)
        group_context = response.context['page_obj'][0].group.title
        self.assertNotEqual(
            group_context,
            group.title,
            (f'Созданный пост попал в неверную группу {group.title}'
             f'вместо {self.post.group.title}')
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='user-p')
        cls.group = Group.objects.create(
            title='title-p',
            slug='slug-p',
            description='description-p'
        )
        text = 'Тестовый текст для 13-ти постов для проверки паджинатора'
        for i in range(13):
            Post.objects.create(
                text=text,
                author=PaginatorViewsTest.author,
                group=PaginatorViewsTest.group,
            )

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.author)

    def test_paginate_1(self):
        """
        Работа паджинатора (количество постов
        на первой страничке, проверяем главную, отфильрованную по группам
        и профайл).
        """
        url_gr = reverse('posts:group_list', kwargs={'slug': self.group.slug})
        url_pr = reverse('posts:profile', args=[self.author.username],)
        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.author_client.get(url_gr)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.author_client.get(url_pr)
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginate_2(self):
        """
        Работы паджинатора (количество постов на второй страничке).
        """
        response = self.author_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
