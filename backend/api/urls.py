from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)
router.register('ingredients', views.IngredientViewSet)
router.register('tags', views.TagViewSet)
router.register('users', views.UserViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('docs/openapi-schema.yml', views.openapi_schema_view, name='openapi-schema'),
    path('docs/', views.redoc_view, name='redoc'),
    path('', include(router.urls)),
]