from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='products')

urlpatterns = [
    path('auth/register/', views.register_view),
    path('auth/login/', views.login_view),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('users/', views.users_list),
    path('users/<int:pk>/', views.user_detail),
    path('users/<int:pk>/permissions/', views.user_permissions),
    path('cart/', views.cart_view),
    path('cart/items/', views.cart_items_create),
    path('cart/items/<int:pk>/', views.cart_item_detail),
    path('cart/checkout/', views.cart_checkout),
    path('orders/', views.orders_list),
    path('', include(router.urls)),
]