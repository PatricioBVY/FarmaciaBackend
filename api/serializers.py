from rest_framework import serializers
from .models import User, Product, CartItem, Order, DEFAULT_PERMISSIONS

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'run', 'first_name', 'last_name', 'role', 'is_active']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = User
        fields = ['id', 'email', 'run', 'password', 'first_name', 'last_name', 'region', 'commune', 'address']

    def validate_email(self, value):
        email = value.strip().lower()
        allowed = ('@duoc.cl', '@profesor.duoc.cl', '@gmail.com')
        if not email.endswith(allowed):
            raise serializers.ValidationError("Solo se permiten correos @duoc.cl, @profesor.duoc.cl o @gmail.com.")
        return email

    def create(self, validated_data):
        return User.objects.create_user(
            role='usuario',
            is_active=True,
            permissions=DEFAULT_PERMISSIONS.copy(),
            **validated_data
        )

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'category', 'is_offer']

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_detail', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'total', 'items_snapshot', 'created_at']