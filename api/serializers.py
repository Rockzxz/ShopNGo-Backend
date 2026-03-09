from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Shop, Product, Order, OrderItem, UserProfile, Address

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
        fields = ['id', 'title', 'shop', 'price', 'oldPrice', 'rating']

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.ReadOnlyField(source='product.id')
    title = serializers.ReadOnlyField(source='product.title')
    price = serializers.ReadOnlyField(source='product.price')
    shop = serializers.StringRelatedField(source='product.shop') 

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'title', 'price', 'shop', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'is_completed', 'items']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'label', 'phone_number', 'full_address', 'is_default']