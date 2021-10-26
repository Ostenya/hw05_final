from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост без указания группы',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        test_user = PostModelTests.user
        test_group = PostModelTests.group
        test_post = PostModelTests.post
        model_strs = {
            test_user: 'auth',
            test_post: 'Тестовый пост б',
            test_group: 'Тестовая группа',
        }
        for object, expected_value in model_strs.items():
            with self.subTest(field=expected_value):
                self.assertEqual(str(object), expected_value)

    def test_model_post_verbose_names(self):
        test_post = PostModelTests.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_model_post_help_texts(self):
        test_post = PostModelTests.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_post._meta.get_field(field).help_text,
                    expected_value
                )
