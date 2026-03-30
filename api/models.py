from django.contrib.auth.models import User
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="grid") 

    def __str__(self):
        return self.name

class Shop(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop', null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    
    logo = models.ImageField(upload_to='shop_logos/', null=True, blank=True)
    description = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=200)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    oldPrice = models.CharField(max_length=50, blank=True, null=True) 
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    
    # --- ADDED FOR THE WEBSITE MERCHANTS ---
    description = models.TextField(blank=True, null=True)
    image_url = models.ImageField(upload_to='products/', null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Confirmed', 'Confirmed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    address_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username} ({self.status})"

class OrderItem(models.Model):
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
    
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.title}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5) # 1-5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"