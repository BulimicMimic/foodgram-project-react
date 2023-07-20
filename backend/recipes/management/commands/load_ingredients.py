import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient

from api.serializers import IngredientLoadSerializer


class Command(BaseCommand):
    help = 'Загрузка ингредиентов.'

    def handle(self, *args, **options):
        with open(f'{settings.BASE_DIR}/data/ingredients.csv',
                  'r',
                  encoding='utf-8',
                  ) as csv_file:
            reader = csv.DictReader(csv_file)
            ingredient_list = []
            csv_errors = 0
            for csv_data in reader:
                serializer = IngredientLoadSerializer(
                    data={**csv_data},
                )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    ingredient_list.append(Ingredient(**csv_data))
                else:
                    csv_errors += 1

            try:
                Ingredient.objects.bulk_create(ingredient_list)
            except IntegrityError:
                return 'Такой ингредиент уже существует.'
        return (f'Загружено {Ingredient.objects.count()} ингредиентов.'
                f'Ошибок в csv файле - {csv_errors}')
