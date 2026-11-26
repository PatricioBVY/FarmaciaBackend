from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

DEFAULT_PERMISSIONS = {
    "ver-productos": True,
    "comprar": True,
    "ver-carrito": True,
    "acceso-admin": False,
    "editar-perfil": True,
    "ver-historial": False,
}

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("permissions", DEFAULT_PERMISSIONS.copy())
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('usuario', 'Usuario'), ('moderador', 'Moderador'), ('admin', 'Admin')]
    email = models.EmailField(unique=True)
    run = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    commune = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='usuario')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    permissions = models.JSONField(default=dict)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['run']

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    image = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    is_offer = models.BooleanField(default=False)

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total = models.PositiveIntegerField()
    items_snapshot = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
