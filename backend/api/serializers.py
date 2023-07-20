import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import EmailValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    MIN_AMOUNT,
    Recipe,
    ShoppingCart,
    Tag,
)

from api.validators import validate_username

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[validate_username,
                    UniqueValidator(queryset=User.objects.all()),
                    ]
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[EmailValidator(),
                    UniqueValidator(queryset=User.objects.all()),
                    ]
    )
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.followed_by.filter(user=user).exists()

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientLoadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True,
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(many=True,
                                           read_only=True,
                                           source='ingredients_amounts',
                                           )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.choice.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.purchase.filter(user=user).exists()


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(many=True,
                                            source='ingredients_amounts',
                                            )
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True,
                                              )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        seen_ingredient = set()
        dupes_ingredient = []
        for ingredient in data['ingredients_amounts']:
            if ingredient['amount'] < MIN_AMOUNT:
                raise serializers.ValidationError(
                    'Минимальное количество ингредиента должно быть больше 0.'
                )
            if ingredient['id'] in seen_ingredient:
                dupes_ingredient.append(ingredient['id'])
            else:
                seen_ingredient.add(ingredient['id'])
        if dupes_ingredient:
            raise serializers.ValidationError(
                'Нельзя добавить в рецепт два одинаковых ингредиента.'
            )
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients_amounts')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags)
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(Ingredient,
                                                   id=ingredient['id'])
            amount = ingredient['amount']
            ingredient_list.append(
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=amount,
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_list)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients_amounts')
        tags = validated_data.pop('tags')
        instance.ingredients_amounts.all().delete()

        instance.tags.set(tags)
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(Ingredient,
                                                   id=ingredient['id'])
            amount = ingredient['amount']
            ingredient_list.append(
                IngredientRecipe(
                    recipe=instance,
                    ingredient=current_ingredient,
                    amount=amount,
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_list)
        return super().update(instance, validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в избранном.'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': request},
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в списке покупок.'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': request},
        ).data


class SubscribeRepresentationSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.followed_by.filter(user=user).exists()

    def get_recipes(self, obj):
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        recipes_list = obj.recipes.all()
        if recipes_limit:
            recipes_list = recipes_list[:int(recipes_limit)]
        return RecipeShortSerializer(recipes_list, many=True,
                                     context={'request': request}
                                     ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Такая подписка уже есть.'
            )
        ]

    def validate(self, obj):
        if obj['author'] == obj['user']:
            raise serializers.ValidationError(
                'Нельзя оформить подписку на самого себя!'
            )
        return obj

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscribeRepresentationSerializer(
            instance.author,
            context={'request': request},
        ).data
