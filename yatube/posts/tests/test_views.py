import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.db.models.fields.files import ImageFieldFile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from posts.models import Post, Group, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_auth')
        cls.user2 = User.objects.create_user(username='test_auth2')
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='Test_slug_1',
            description='Тестовое описание группы 1',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='Test_slug_2',
            description='Тестовое описание группы 2',
        )
        cls.posts = []
        for i in range(44):
            if i % 3 == 0:
                obj = Post(
                    author=cls.user2,
                    text=f'Тестовый пост № {i} без группы',
                )
            elif i % 3 == 1:
                obj = Post(
                    author=cls.user,
                    group=cls.group1,
                    text=(f'Тестовый пост № {i} в группе {cls.group1.title}'),
                )
            else:
                obj = Post(
                    author=cls.user,
                    group=cls.group2,
                    text=(f'Тестовый пост № {i} в группе {cls.group2.title}'),
                )
            cls.posts.append(obj)
        cls.posts = Post.objects.bulk_create(cls.posts)
        cls.posts_num = Post.objects.count()
        cls.posts_group1_num = cls.group1.posts.count()
        cls.posts_user_num = cls.user.posts.count()
        cls.views = {
            reverse('posts:index'): {
                'template': 'posts/index.html',
                'context': 'page_obj',
                'posts_num': cls.posts_num,
            },
            reverse('posts:group_list', kwargs={
                    'slug': cls.group1.slug}): {
                'template': 'posts/group_list.html',
                'context': 'page_obj',
                'posts_num': cls.posts_group1_num,
            },
            reverse('posts:profile', kwargs={
                    'username': cls.user.username}): {
                'template': 'posts/profile.html',
                'context': 'page_obj',
                'posts_num': cls.posts_user_num,
            },
            reverse('posts:post_detail', kwargs={
                    'post_id': cls.user.posts.last().id}): {
                'template': 'posts/post_detail.html',
                'context': 'post',
            },
            reverse('posts:post_create'): {
                'template': 'posts/create_post.html',
                'context': 'form',
            },
            reverse('posts:post_edit', kwargs={
                    'post_id': cls.user.posts.last().id}): {
                'template': 'posts/create_post.html',
                'context': 'form',
            },
        }
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.authorized_client = Client()
        self.author_client.force_login(PostViewsTests.user)
        self.authorized_client.force_login(PostViewsTests.user2)

    def test_posts_templates_views(self):
        """Во view-функциях используются правильные html-шаблоны."""
        for reverse_name, expected in PostViewsTests.views.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, expected['template'])

    def test_posts_index_correct_context(self):
        """В шаблон view-функции index передан правильный контекст."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][1]
        expected_objects = Post.objects.all()
        self.assertIn(first_object, expected_objects)

    def test_posts_group_posts_correct_context(self):
        """В шаблон view-функции group_posts передан правильный контекст."""
        response = self.guest_client.get(reverse('posts:group_list', kwargs={
            'slug': PostViewsTests.group1.slug}))
        first_object = response.context['page_obj'][1]
        expected_objects = PostViewsTests.group1.posts.all()
        self.assertIn(first_object, expected_objects)

    def test_posts_profile_correct_context(self):
        """В шаблон view-функции profile передан правильный контекст."""
        response = self.guest_client.get(reverse('posts:profile', kwargs={
            'username': PostViewsTests.user.username}))
        first_object = response.context['page_obj'][1]
        expected_objects = PostViewsTests.user.posts.all()
        self.assertIn(first_object, expected_objects)

    def test_posts_post_detail_correct_context(self):
        """В шаблон view-функции post_detail передан правильный контекст."""
        response = self.guest_client.get(reverse('posts:post_detail', kwargs={
            'post_id': Post.objects.last().id}))
        object = response.context['post']
        form_text = response.context['form'].fields.get('text')
        expected_object = Post.objects.last()
        self.assertEqual(
            object,
            expected_object,
            'В шаблон view-функции post_detail передан неправильный пост'
        )
        self.assertIsInstance(
            form_text,
            forms.fields.CharField,
            'В шаблон view-функции post_detail передана неправильная форма'
        )

    def test_posts_create_correct_context(self):
        """В шаблон view-функции post_create передан правильный контекст."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
        }
        for attr, expected in form_fields.items():
            with self.subTest(attr=attr):
                form_field = response.context.get('form').fields.get(attr)
                self.assertIsInstance(form_field, expected)

    def test_posts_edit_correct_context(self):
        """В шаблон view-функции post_edit передан правильный контекст."""
        post = Post.objects.filter(
            author=PostViewsTests.user).latest('id')
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id}))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
        }
        for attr, expected in form_fields.items():
            with self.subTest(attr=attr):
                form_field = response.context.get('form').fields.get(attr)
                self.assertIsInstance(
                    form_field,
                    expected,
                    ('В шаблон view-функции post_edit'
                     'передана неправильная форма')
                )
                self.assertEqual(
                    post.id,
                    response.context['post_id'],
                    ('В шаблон view-функции post_edit'
                     'передан неправильный пост')
                )

    def test_first_page_contains_ten_records(self):
        """Проверка того, что количество постов на 1 странице = 10."""
        for reverse_name, expected in PostViewsTests.views.items():
            if expected['context'] == 'page_obj':
                with self.subTest(reverse_name=reverse_name):
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(len(response.context['page_obj']), 10)

    def test_last_page_contains_left_records(self):
        """Проверка того, что количество постов на последней странице
        = остатку.
        """
        for reverse_name, expected in PostViewsTests.views.items():
            if expected['context'] == 'page_obj':
                with self.subTest(reverse_name=reverse_name):
                    last_page_num = expected['posts_num'] // 10 + 1
                    posts_last_num = expected['posts_num'] % 10
                    response = self.guest_client.get(
                        reverse_name + f'?page={last_page_num}')
                    self.assertEqual(
                        len(response.context['page_obj']),
                        posts_last_num
                    )

    def test_last_post_on_pages(self):
        """Проверка того, что если при создании поста указать группу,
        то этот пост появляется:
        - на главной странице сайта,
        - на странице выбранной группы,
        - в профайле пользователя.
        """
        new_post1 = Post.objects.create(
            author=PostViewsTests.user,
            group=PostViewsTests.group1,
            text=f'Новый Пост 1 в группе {PostViewsTests.group1.title}',
        )
        for reverse_name, expected in PostViewsTests.views.items():
            with self.subTest(reverse_name=reverse_name):
                if expected['context'] == 'page_obj':
                    response = self.guest_client.get(reverse_name)
                    self.assertIn(
                        new_post1,
                        response.context['page_obj'].object_list
                    )

    def test_last_post_not_on_wrong_page(self):
        """Проверка того, что если при создании поста указать группу,
        то этот пост не попал в группу, для которой не был предназначен.
        """
        new_post2 = Post.objects.create(
            author=PostViewsTests.user,
            group=PostViewsTests.group1,
            text=f'Новый Пост 2 в группе {PostViewsTests.group1.title}',
        )
        response = self.guest_client.get(reverse('posts:group_list', kwargs={
            'slug': PostViewsTests.group2.slug}))
        self.assertNotIn(new_post2, response.context['page_obj'].object_list)

    def test_last_post_with_image_on_pages(self):
        """Проверка того, что если при создании поста прикрепить картинку,
        то изображение передаётся в словаре context:
        - на главной странице сайта,
        - на странице выбранной группы,
        - в профайле пользователя,
        - на отдельной странице поста.
        """
        post_image = Post.objects.create(
            author=PostViewsTests.user,
            group=PostViewsTests.group1,
            text='Тестовый пост с картинкой в тестовой группе 1',
            image=PostViewsTests.uploaded
        )
        for reverse_name, expected in PostViewsTests.views.items():
            with self.subTest(reverse_name=reverse_name):
                if expected['context'] == 'page_obj':
                    response = self.guest_client.get(reverse_name)
                    self.assertIn(
                        post_image,
                        response.context['page_obj'].object_list
                    )
                elif expected['context'] == 'post':
                    response = self.guest_client.get(reverse(
                        'posts:post_detail',
                        kwargs={
                            'post_id': PostViewsTests.user.posts.first().id
                        }
                    )
                    )
                    object = response.context['post']
                    self.assertIsInstance(object.image, ImageFieldFile)

    def test_comment_on_post_page(self):
        """Проверка того, что после успешной отправки комментарий
        появляется на странице поста.
        """
        post = Post.objects.last()
        new_comment = Comment.objects.create(
            author=PostViewsTests.user,
            post=Post.objects.last(),
            text=f'Новый комментарий к посту {post.text[:10]}',
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        ))
        self.assertIn(new_comment, response.context['post'].comments.all())

    def test_authorized_client_follow(self):
        """Проверка того, что авторизованный пользователь может подписываться
        на других пользователей.
        """
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostViewsTests.user.username}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewsTests.user2,
                author=PostViewsTests.user,
            ).exists(),
            'Авторизованный пользователь не может подписываться на других'
        )

    def test_authorized_client_unfollow(self):
        """Проверка того, что авторизованный пользователь может
        удалять других пользователей из подписок.
        """
        Follow.objects.get_or_create(
            user=PostViewsTests.user2,
            author=PostViewsTests.user,
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostViewsTests.user.username}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTests.user2,
                author=PostViewsTests.user,
            ).exists(),
            'Авторизованный пользователь не может удалить из подписки'
        )

    def test_authorizes_client_follow_index_page(self):
        """Проверка того, что новая запись пользователя появляется
        в ленте тех, кто на него подписан, и не появляется в ленте
        тех, кто не подписан.
        """
        Follow.objects.create(
            user=PostViewsTests.user2,
            author=PostViewsTests.user,
        )
        new_post = Post.objects.create(
            author=PostViewsTests.user,
            text='Новая запись пользователя',
        )
        user2_follow_page = self.authorized_client.get(
            reverse('posts:follow_index'))
        user_follow_page = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(
            new_post,
            user2_follow_page.context['page_obj'].object_list,
            'Новая запись пользователя не появляется в ленте подписчика'
        )
        self.assertNotIn(
            new_post,
            user_follow_page.context['page_obj'].object_list,
            'Новая запись пользователя не появляется в ленте неподписчика'
        )


class PostViewsCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_auth')

    def setUp(self):
        self.guest_client = Client()

    def test_posts_cash_on_pages(self):
        """Проверка того, что список постов хранится в кеше 20 секунд:
        - на главной странице сайта.
        """
        new_post = Post.objects.create(
            author=PostViewsCacheTests.user,
            text='Новый Пост для проверки кеша',
        )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(
            new_post,
            response.context['page_obj'].object_list,
            'Пост из БД не отображается на странице'
        )
        new_post.delete()
        self.assertFalse(
            Post.objects.filter(
                author=PostViewsCacheTests.user,
                text='Новый Пост для проверки кеша',
            ).exists(),
            'Пост из БД не удалился'
        )
        response2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            response.content,
            response2.content,
            'Пост из кеша не отображается в контенте страницы'
        )
        cache.clear()
        response3 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(
            response2.content,
            response3.content,
            'Пост из кеша не удалился из контента страницы'
        )
