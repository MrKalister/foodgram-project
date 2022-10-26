#!-*-coding:utf-8-*-
import base64
import json
import tempfile

from PIL import Image
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from recipes.models import Ingredient, Tag, Recipe
from users.models import User


class ReciepeViewTestCase(TestCase):
    """Тест api рецептов."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('api:recipes-list')
        cls.user = User.objects.create_user(
            username='admin',
            password='admin',
            first_name='egor',
            last_name='letov',
        )
        cls.api_client = APIClient()
        cls.token = Token.objects.create(user=cls.user)

    def setUp(self) -> None:
        self.amount = 22
        self.ing_salt = Ingredient.objects.create(
            name='salt',
            measurement_unit='g'
        )
        self.tag1 = Tag.objects.create(
            name='tag1',
            color='red',
            slug='tag1',
        )
        self.tag2 = Tag.objects.create(
            name='tag2',
            color='blue',
            slug='tag2',
        )

        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(self.tmp_file.name)

        self.api_client.force_authenticate(user=self.user, token=self.token)

    def create_recipe(self, **kw):
        data = {
            'name': 'salat',
            'text': 'text',
            'cooking_time': 4,
            'author': self.user,
        }
        data.update(kw)

        recipe = Recipe.objects.create(**data)

        recipe.tags.add(self.tag1)
        recipe.ingredients.add(
            self.ing_salt,
            through_defaults={'amount': self.amount}
        )
        return recipe

    def test_create_recipe(self):
        """Тест создания рецепта.
        """
        data = {
            "ingredients": [
                {
                    "id": self.ing_salt.id,
                    "amount": 10,
                },
            ],
            "tags": [self.tag1.pk, self.tag2.pk],
            "name": "pay",
            "text": "cook pay",
            "cooking_time": 1,
            "image": base64.b64encode(self.tmp_file.read()).decode('utf-8'),
        }

        resp = self.api_client.post(path=self.url,
                                    data=json.dumps(data),
                                    content_type='application/json',
                                    )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.last()
        self.assertEqual(resp.data.get('id'), recipe.id)
        self.assertEqual(recipe.ingredients.last().id, self.ing_salt.id)

    def test_list(self):
        recipe = self.create_recipe()

        resp = self.api_client.get(self.url)

        resp_data = resp.json()['results'][0]
        self.assertEqual(resp_data['name'], recipe.name)

        ing_data = resp_data['ingredients'][0]
        self.assertEqual(ing_data['id'], recipe.ingredients.last().id)
        self.assertEqual(ing_data['amount'], self.amount)
