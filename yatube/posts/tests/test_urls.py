from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_auth')
        cls.noname_user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост c указанием группы',
        )
        cls.urls_all = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }

        cls.urls_author = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html'
        }
        cls.urls_authorized = {
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            f'/profile/{cls.user.username}/follow/': '',
            f'/profile/{cls.user.username}/unfollow/': '',
            f'/posts/{cls.post.id}/comment/': '',
        }
        cls.urls_no = {'/unexisting_page': 'core/404.html', }

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.noname_user)

    def test_posts_urls_all(self):
        """Проверка доступности страниц приложения posts для всех."""
        for url in PostURLTests.urls_all:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_posts_urls_author(self):
        """Проверка доступности страниц приложения posts для автора."""
        for url in PostURLTests.urls_author:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_posts_urls_authorized(self):
        """Проверка доступности страниц приложения posts для авторизованного
        пользователя.
        """
        for url, template in PostURLTests.urls_authorized.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if not template == '':
                    self.assertEqual(response.status_code, 200)

    def test_posts_urls_no(self):
        """Проверка недоступности несуществующих страниц приложения posts."""
        for url in PostURLTests.urls_no:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_posts_templates_all(self):
        """Проверка корректности шаблонов приложения posts для всех."""
        for url, template in PostURLTests.urls_all.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_posts_templates_author(self):
        """Проверка корректности шаблонов приложения posts для автора."""
        for url, template in PostURLTests.urls_author.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_posts_templates_authorized(self):
        """Проверка корректности шаблонов приложения posts для авторизованного
        пользователя.
        """
        for url, template in PostURLTests.urls_authorized.items():
            with self.subTest(url=url):
                if not template == '':
                    response = self.authorized_client.get(url)
                    self.assertTemplateUsed(response, template)

    def test_posts_templates_no(self):
        """Проверка того, что страница 404 отдает кастомный шаблон."""
        for url, template in PostURLTests.urls_no.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
