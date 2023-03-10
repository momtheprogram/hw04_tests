import pytest
from mixer.backend.django import mixer as _mixer
from posts.models import Group, Post


@pytest.fixture
def mixer():
    return _mixer


@pytest.fixture
def post(user):
    from posts.models import Post
    return Post.objects.create(text='Тестовый пост 1', author=user)


@pytest.fixture
def group():
    from posts.models import Group
    return Group.objects.create(title='Тестовая группа 1', slug='test-link', description='Тестовое описание группы')


@pytest.fixture
def post_with_group(user, group):
    from posts.models import Post
    return Post.objects.create(text='Тестовый пост 2', author=user, group=group)


@pytest.fixture
def few_posts_with_group(mixer, user, group):
    """Return one record with the same author and group."""
    posts = mixer.cycle(20).blend(Post, author=user, group=group)
    return posts[0]
