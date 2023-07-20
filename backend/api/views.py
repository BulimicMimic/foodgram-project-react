from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import (
    IsCurrentUserOrAdminOrReadOnly,
    IsOwnerOrAdminOrReadOnly,
)
from api.serializers import (
    SubscribeSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    SubscribeRepresentationSerializer,
    UserSerializer,
)

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve',):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated, ],
            )
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже есть в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST,
                                )
            serializer = FavoriteSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепта нет в избранном.'},
                                status=status.HTTP_404_NOT_FOUND,
                                )
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response('Рецепт успешно удалён из избранного.',
                            status=status.HTTP_204_NO_CONTENT
                            )

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated, ],
            )
    def shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже есть в списке покупок'},
                                status=status.HTTP_400_BAD_REQUEST,
                                )
            serializer = ShoppingCartSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(user=user,
                                               recipe=recipe).exists():
                return Response({'errors': 'Рецепта нет в списке покупок.'},
                                status=status.HTTP_404_NOT_FOUND,
                                )
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response('Рецепт успешно удалён из списка покупок.',
                            status=status.HTTP_204_NO_CONTENT,
                            )

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated, ],
            )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.client.exists():
            return Response('Вы ничего не добавляли в список покупок.',
                            status=status.HTTP_404_NOT_FOUND,
                            )
        ingredients = (
            IngredientRecipe.objects
            .filter(recipe__purchase__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(full_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list = 'Foodgram представляет вам список ингридентов, '
        shopping_list += 'необходимых для выбранных вами блюд:\n'
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['full_amount']
            shopping_list += f'\n{name} - {amount}, {measurement_unit}'
        shopping_list += '\n\nСпасибо что воспользовались Foodgram!'
        filename = 'shopping_cart.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    pagination_class = None


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsCurrentUserOrAdminOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == "set_password":
            return SetPasswordSerializer
        return UserSerializer

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(['post'], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        return Response('Пароль упешно изменен.',
                        status=status.HTTP_204_NO_CONTENT,
                        )

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated, ],
            )
    def subscribe(self, request, pk):
        user = self.request.user
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response({'errors': 'Такая подписка уже есть.'},
                                status=status.HTTP_400_BAD_REQUEST,
                                )
            serializer = SubscribeSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Follow.objects.filter(user=user, author=author).exists():
                return Response({'errors': 'Объект не найден.'},
                                status=status.HTTP_404_NOT_FOUND,
                                )
            Follow.objects.filter(user=user, author=author).delete()
            return Response('Успешная отписка.',
                            status=status.HTTP_204_NO_CONTENT
                            )

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated, ],
            )
    def subscriptions(self, request):
        user = self.request.user
        authors = User.objects.filter(followed_by__user=user).all()
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscribeRepresentationSerializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscribeRepresentationSerializer(
            authors,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
