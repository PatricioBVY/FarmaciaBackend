from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Product, Cart, CartItem, Order, DEFAULT_PERMISSIONS
from .serializers import UserSerializer, RegisterSerializer, ProductSerializer, CartItemSerializer, OrderSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = str(request.data.get('email', '')).strip().lower()
    password = request.data.get('password', '')
    user = User.objects.filter(email=email).first()
    if not user or not user.check_password(password):
        return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({'detail': 'Usuario bloqueado o inactivo.'}, status=status.HTTP_403_FORBIDDEN)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    })

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'moderador']:
            return Response({'detail': 'Sin permisos.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'moderador']:
            return Response({'detail': 'Sin permisos.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'moderador']:
            return Response({'detail': 'Sin permisos.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_list(request):
    if request.user.role not in ['admin', 'moderador']:
        return Response({'detail': 'Sin autorización.'}, status=status.HTTP_403_FORBIDDEN)
    qs = User.objects.all().order_by('id')
    if request.user.role == 'moderador':
        qs = qs.exclude(role='admin')
    return Response(UserSerializer(qs, many=True).data)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    if request.user.role not in ['admin', 'moderador']:
        return Response({'detail': 'Sin autorización.'}, status=status.HTTP_403_FORBIDDEN)
    target = get_object_or_404(User, pk=pk)
    if request.user.role == 'moderador' and (target.role == 'admin' or request.data.get('role') == 'admin'):
        return Response({'detail': 'Un moderador no puede modificar ni asignar administradores.'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'PATCH':
        serializer = UserSerializer(target, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    return Response(UserSerializer(target).data)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_permissions(request, pk):
    if request.user.role != 'admin':
        return Response({'detail': 'Solo admin puede gestionar permisos.'}, status=status.HTTP_403_FORBIDDEN)
    target = get_object_or_404(User, pk=pk)
    perms = {**DEFAULT_PERMISSIONS, **(target.permissions or {})}
    if request.method == 'PATCH':
        incoming = request.data.get('permissions', {})
        perms.update({k: bool(v) for k, v in incoming.items() if k in DEFAULT_PERMISSIONS})
        target.permissions = perms
        target.save()
    return Response({'permissions': perms})

@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if request.method == 'DELETE':
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    items = cart.items.select_related('product').all().order_by('id')
    serialized = CartItemSerializer(items, many=True).data
    total = sum(item['subtotal'] for item in serialized)
    return Response({'id': cart.id, 'items': serialized, 'total': total})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_items_create(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product_id = request.data.get('product') or request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    product = get_object_or_404(Product, pk=product_id)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()
    return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_item_detail(request, pk):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=pk, cart=cart)
    if request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    quantity = int(request.data.get('quantity', 1))
    if quantity <= 0:
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    item.quantity = quantity
    item.save()
    return Response(CartItemSerializer(item).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related('product').all())
    if not items:
        return Response({'detail': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)
    serialized = CartItemSerializer(items, many=True).data
    total = sum(i['subtotal'] for i in serialized)
    order = Order.objects.create(user=request.user, total=total, items_snapshot=serialized)
    cart.items.all().delete()
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return Response(OrderSerializer(orders, many=True).data)