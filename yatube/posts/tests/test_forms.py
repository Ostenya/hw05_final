import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_slug',
            description='Тестовое описание группы',
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='Тестовый пост № 1 без группы',
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            text='Тестовый пост № 2 в тестовой группе',
            group=cls.group,
        )
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
        cls.form_data = {
            'text': 'Тестовый пост № 3 в тестовой группе',
            'group': PostFormsTests.group.id,
            'image': cls.uploaded,
        }
        cls.form_data_comment = {
            'text': 'Тестовый коммент',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostFormsTests.user)

    def test_posts_create_form(self):
        """При отправке валидной формы со страницы создания поста
        reverse('posts:create_post') создаётся новая запись в базе данных.
        """
        posts_num = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=PostFormsTests.form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': PostFormsTests.user.username}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_num + 1)
        # Проверяем, что создалась запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text=PostFormsTests.form_data['text'],
                group=PostFormsTests.group,
                author=PostFormsTests.user,
                image='posts/small.gif'
            ).exists()
        )

    def test_posts_edit_form(self):
        """При отправке валидной формы со страницы редактирования поста
        reverse('posts:post_edit', args=('post_id',)) происходит
        изменение поста с post_id в базе данных.
        """
        posts_num = Post.objects.count()
        post = PostFormsTests.post1
        form_data = {
            'text': 'Изменённый Тестовый пост № 1 - в тестовой группе',
            'group': PostFormsTests.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': post.id}))
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_num)
        # Проверяем, что запись изменилась
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=PostFormsTests.group,
                author=PostFormsTests.user
            ).exists()
        )

    def test_add_comment_form_author(self):
        """При отправке валидной формы создания коммента авторизованным
        пользователем создаётся новая запись в комментах поста.
        """
        post = PostFormsTests.post1
        comments_num = post.comments.count()
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=PostFormsTests.form_data_comment,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': post.id}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(post.comments.count(), comments_num + 1)
        # Проверяем, что создалась запись с заданным текстом
        self.assertTrue(
            post.comments.filter(
                text=PostFormsTests.form_data_comment['text'],
                author=PostFormsTests.user,
            ).exists()
        )

    def test_no_add_comment_form_guest(self):
        """При попытке отправить форму создания коммента неавторизованным
        пользователем осуществляется редирект на страницу авторизации.
        """
        post = PostFormsTests.post1
        comments_num = post.comments.count()
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=PostFormsTests.form_data_comment,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, (reverse(
            'users:login') + f'?next=%2Fposts%2F{post.id}%2Fcomment%2F'))
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(post.comments.count(), comments_num)
