from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['username', 'email']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'author', 'cooking_time', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'author']
    list_filter = ['author']

admin.site.register(Favorite)
admin.site.register(ShoppingCartItem)
admin.site.register(RecipeIngredient)
