from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Shop, Product, Order, OrderItem, UserProfile, Address, Wishlist

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # 1. Create the core user
        user = User.objects.create_user(
            username=validated_data['email'], 
            email=validated_data['email'],
            password=validated_data['password']
        )
        # 2. Force Django to save the name and update the database
        user.first_name = validated_data.get('first_name', '')
        user.save()
        
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon']

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'category']

class ProductSerializer(serializers.ModelSerializer):
    # This ensures the API sends the shop's name (e.g., "Local Meats") 
    # instead of just the shop's ID number, which the frontend expects!
    shop = serializers.StringRelatedField() 

    class Meta:
        model = Product
        # --- UPDATED: Added category, description, image_url, and stock_quantity ---
        fields = [
            'id', 'title', 'shop', 'category', 'price', 
            'oldPrice', 'rating', 'description', 'image_url', 'stock_quantity'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.ReadOnlyField(source='product.id')
    title = serializers.ReadOnlyField(source='product.title')
    price = serializers.ReadOnlyField(source='product.price')
    shop = serializers.StringRelatedField(source='product.shop') 
    
    # Optional but helpful: Added image_url so the cart screen can show product images!
    image_url = serializers.ReadOnlyField(source='product.image_url')

    class Meta:
        model = OrderItem
        # --- UPDATED: Added image_url to the cart items ---
        fields = ['id', 'product_id', 'title', 'price', 'shop', 'quantity', 'image_url']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'is_completed', 'items']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'label', 'phone_number', 'full_address', 'is_default']

class WishlistSerializer(serializers.ModelSerializer):
    # This pulls the full product data instead of just the ID
    product = ProductSerializer(read_only=True) 

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'created_at']