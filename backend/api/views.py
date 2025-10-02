from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.filters import SearchFilter

from food.models import (
    Recipe, Ingredient, Tag, User,
    Follow, Favorite, ShoppingCartItem
)
from .serializers import (
    RecipeReadSerializer, RecipeWriteSerializer, IngredientSerializer,
    TagSerializer, UserSerializer, UserAvatarSerializer, SubscribeSerializer
)
from django.http import HttpResponse


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tags', 'author']

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(favorites__user=user)
            elif is_favorited == '0':
                queryset = queryset.exclude(favorites__user=user)
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart and user.is_authenticated:
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(shopping_cart__user=user)
            elif is_in_shopping_cart == '0':
                queryset = queryset.exclude(shopping_cart__user=user)
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            Favorite.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        else:
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            ShoppingCartItem.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        else:
            ShoppingCartItem.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        return Response({"detail": "Функционал в разработке"})


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['^name']
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        return super().me(request)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        author_id = kwargs['id']
        author = get_object_or_404(User, pk=author_id)
        
        if request.method == 'POST':
            Follow.objects.get_or_create(follower=request.user, author=author)
            return Response(status=status.HTTP_201_CREATED)
        else:
            Follow.objects.filter(follower=request.user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        follows = Follow.objects.filter(follower=request.user)
        authors = [follow.author for follow in follows]
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscribeSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = SubscribeSerializer(authors, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False,
            methods=['put'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        serializer = UserAvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        serializer = UserAvatarSerializer(
            request.user,
            data={},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def redoc_view(request):
    """View для отображения документации Redoc"""
    redoc_path = '/app/static/redoc/redoc.html'
    
    try:
        with open(redoc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content)
    except FileNotFoundError:
        return HttpResponse(f"Redoc file not found at: {redoc_path}", status=404)

def openapi_schema_view(request):
    """View для отдачи схемы OpenAPI"""
    schema_path = '/app/static/redoc/openapi-schema.yml'
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = HttpResponse(content, content_type='application/x-yaml')
        return response
    except FileNotFoundError:
        return HttpResponse(f"Schema file not found at: {schema_path}", status=404)
