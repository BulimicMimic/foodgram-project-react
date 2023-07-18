from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (IngredientViewSet,
                    RecipeViewSet,
                    TagViewSet,
                    UserViewSet,
                    )

router_v1 = SimpleRouter()
router_v1.register('ingredients', IngredientViewSet)
router_v1.register('tags', TagViewSet)
router_v1.register('recipes', RecipeViewSet)
router_v1.register('users', UserViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
