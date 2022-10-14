import os
from django.core.management.base import BaseCommand
import json
from recipes.models import Ingredient
from foodgram.settings import CSV_FILES_DIR

    
class Command(BaseCommand):
    def handle(self, *args, **options):
        json_path = os.path.join(CSV_FILES_DIR, 'ingredients.json')
        try:
            with open(json_path, 'rb') as f:
                data = json.load(f)
                for i in data:
                    print(i)
                    ingredient = Ingredient()
                    ingredient.name = i['name']
                    ingredient.measurement_unit = i['measurement_unit']
                    ingredient.save()
            print('finished')
        except FileNotFoundError:
            print(f'Файл \'ingredients.json\' не найден.')
            return
        