from django.contrib.auth.models import User
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Shop(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=200)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    
    # --- NEW: Link the product directly to a category ---
    # We use null=True, blank=True so your existing products don't cause a database crash!
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    oldPrice = models.CharField(max_length=50, blank=True, null=True) 
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)

    def __str__(self):
        return self.title

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # is_completed: False = Cart, True = Paid/History Order
    is_completed = models.BooleanField(default=False) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    address_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username} ({self.status})"

class OrderItem(models.Model):
    # This now correctly references the single Order model above
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Home') 
    phone_number = models.CharField(max_length=20)
    full_address = models.TextField()
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} - {self.user.username}"