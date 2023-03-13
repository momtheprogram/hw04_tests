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
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Test_title',
            slug='test_slug',
            description='test_description'
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

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """Проверка использования URL-адресом соответствующего шаблона."""
        author_username = PostPagesTests.author.username
        post_id = PostPagesTests.post.pk
        args = {'kwargs': {'slug': PostPagesTests.group.slug},
                'author': {author_username},
                'id': {post_id},
                }
        urls = {'group': 'posts/group_list.html',
                'profile': 'posts/profile.html',
                'detail': 'posts/post_detail.html',
                'create': 'posts/create_post.html',
                }
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs=args['kwargs']): urls['group'],
            reverse('posts:profile', args={author_username}): urls['profile'],
            reverse('posts:post_detail', args=args['id']): urls['detail'],
            reverse('posts:post_edit', args=args['id']): urls['create'],
            reverse('posts:post_create'): urls['create'],
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(
                    response,
                    template,
                    (f'Для {reverse_name} используется некорректный шаблон'
                     f' {template}')
                )

    def test_chek_context_index(self):
        """Проверка шаблона index на формирование правильного контекста."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0].text
        self.assertEqual(first_obj, PostPagesTests.post.text)

    def test_chek_context_group_list(self):
        """
        Проверка шаблона group_list на формирование правильного контекста.
        """
        response = (self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PostPagesTests.group.slug})
        ))
        obj_post = response.context['page_obj'][0].group
        obj_group = response.context['group']
        self.assertEqual(
            obj_post.title,
            PostPagesTests.group.title,
            (f'Пост отсутствует на страничке "posts/group_list.html"'
             f' в группе {obj_group}'),
        )

    def test_chek_context_profile(self):
        """ Проверка контекста profile. """
        another_post = Post.objects.create(
            text='Просто текст другого автора',
            author=PostPagesTests.author,
        )
        url = reverse('posts:profile', args=(PostPagesTests.author.username,))

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
        self.assertEqual(context_author, PostPagesTests.author)

    def test_chek_context_post_detail(self):
        """ Проверка контекста post_detail. """
        author_username = PostPagesTests.author
        post_id = PostPagesTests.post.pk
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            args=[post_id]
        ))
        context_post = response.context['post']
        context_count = response.context['post_count']
        self.assertEqual(context_post,
                         PostPagesTests.post,
                         'Неверный пост в контекте post_detail'
                         )
        self.assertEqual(context_count,
                         author_username.posts.count(),
                         'Неверное количеств постов в контексте post_detail'
                         )

    def test_chek_context_create_post_edit(self):
        post_form = PostForm(instance=PostPagesTests.post)
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            args=[PostPagesTests.post.pk]
        ))
        context_form = response.context['form']
        context_is_edit = response.context['is_edit']
        context_post = response.context['post']

        self.assertIsInstance(
            context_form, type(post_form),
            'Некорректная форма'
        )
        self.assertEqual(
            context_is_edit, True,
            'Ожидалось другое значение is_edit.'
        )
        self.assertEqual(
            context_post, PostPagesTests.post,
            'Не верный пост.'
        )
        self.assertEqual(
            context_form.instance, PostPagesTests.post,
            'Не тот пост в форме.'
        )

    def test_chek_context_create_post(self):
        form_type = type(PostForm())
        response = self.authorized_client.get(reverse('posts:post_create'))
        context_form = response.context['form']
        context_is_edit = response.context['is_edit']
        self.assertIsInstance(context_form, form_type,
                              'Ожидалась другая форма.'
                              )
        self.assertEqual(
            context_is_edit,
            False,
            'Неверное значение is_edit.'
        )

    def test_check_post_in_pages_group(self):
        """
        Проверка появления поста на главной странице сайта,
        на странице выбранной группы, в профайле пользователя
        если при создании поста указать группу.
        """
        response1 = self.authorized_client.get(reverse('posts:index'))
        response2 = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PostPagesTests.group.slug}
        ))
        response3 = self.authorized_client.get(reverse(
            'posts:profile',
            args=(PostPagesTests.author.username,)
        ))

        context1 = response1.context['page_obj'][0]
        context2 = response2.context['page_obj'][0].group.title
        context3 = response3.context['page_obj'][0]

        self.assertEqual(
            context1,
            PostPagesTests.post,
            'На главной странице нет созданного с группой поста'
        )
        self.assertEqual(
            context2,
            PostPagesTests.post.group.title,
            f'В группе {PostPagesTests.group.title} нет созданного поста'
        )
        self.assertEqual(
            context3,
            PostPagesTests.post,
            (f'В профайле пользователя {PostPagesTests.author.username}'
             f' нет созданного поста')
        )

    def test_post_not_in_an_outsider_group(self):
        """
        Проверка отсутствия поста в группе, для которой он не был предназначен.
        """
        group = Group.objects.create(
            title='Simple_title',
            slug='simple-slug',
            description='simple_description'
        )
        kwargs = {'slug': PostPagesTests.group.slug}
        url = 'posts:group_list'
        response = self.authorized_client.get(reverse(url, kwargs=kwargs))
        group_context = response.context['page_obj'][0].group.title
        self.assertNotEqual(
            group_context,
            group.title,
            (f'Созданный пост попал в неверную группу {group.title}'
             'вместо {PostPagesTests.post.group.title}')
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
        Проверка корректности работы паджинатора (количества постов
        на первой страничке, проверяем главную, отфильрованную по группам
        и профайл).
        """
        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.author_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTest.group.slug},
        ))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.author_client.get(reverse(
            'posts:profile',
            args=[PaginatorViewsTest.author.username],
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginate_2(self):
        """
        Проверка корректности работы паджинатора
        (количества постов на второй страничке).
        """
        response = self.author_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
