from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet,
                    openapi_schema_view, redoc_view)

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)
router.register('tags', TagViewSet)
router.register('users', UserViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'docs/openapi-schema.yml',
        openapi_schema_view,
        name='openapi-schema'
    ),
    path('docs/', redoc_view, name='redoc'),
    path('', include(router.urls)),
]
