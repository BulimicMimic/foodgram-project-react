from django.contrib import admin

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    TagRecipe,
)

EMPTY_VALUE = '--NONE--'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = EMPTY_VALUE


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = EMPTY_VALUE


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = EMPTY_VALUE


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ingredient', 'recipe', 'amount')
    search_fields = ('ingredient', 'recipe')
    empty_value_display = EMPTY_VALUE


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline, )
    list_display = ('pk', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    empty_value_display = EMPTY_VALUE

    def favorites_count(self, instance):
        return instance.choice.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = EMPTY_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    empty_value_display = EMPTY_VALUE


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'tag', 'recipe')
    search_fields = ('tag', 'recipe')
    empty_value_display = EMPTY_VALUE
