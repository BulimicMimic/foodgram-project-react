import re

from rest_framework.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Нельзя создать пользователя с таким именем.'
        )
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'В имени использованы недопустимые символы.'
        )
