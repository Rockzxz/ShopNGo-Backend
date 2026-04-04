from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Shop, Product, Order, OrderItem, Address, Wishlist, Review

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
        fields = ['id', 'name', 'category', 'logo']


class ProductSerializer(serializers.ModelSerializer):
    
    shop = serializers.ReadOnlyField(source='shop.name')
    
   
    category_name = serializers.ReadOnlyField(source='category.name')

  

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'shop', 
            'category', 'category_name', 
            'description', 'price', 'stock_quantity', 'rating', 'image_url'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), 
        source='product'
    )
    title = serializers.ReadOnlyField(source='product.title')
    price = serializers.ReadOnlyField(source='product.price')
    shop = serializers.StringRelatedField(source='product.shop') 
    shop_id = serializers.ReadOnlyField(source='product.shop.id')
    
    # 🚨 CHANGED: We use a MethodField to handle the Image URL safely
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'title', 'price', 'shop', 'quantity', 'image_url', 'shop_id']

    # This function safely gets the URL of the image as a string
    def get_image_url(self, obj):
        if obj.product.image_url:
            return obj.product.image_url.url # Returns "/media/products/img.jpg"
        return None

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
   
    product = ProductSerializer(read_only=True) 

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'created_at']

class AdminCreateMerchantSerializer(serializers.ModelSerializer):
    shop = ShopSerializer()

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'shop']

    def create(self, validated_data):
        shop_data = validated_data.pop('shop')
        
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            is_staff=False,       
            is_superuser=False    
        )
        
        Shop.objects.create(user=user, **shop_data)
        return user



class MerchantOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    customer_name = serializers.CharField(source='order.user.first_name', read_only=True)
    address = serializers.CharField(source='order.address_text', read_only=True)
    status = serializers.CharField(source='order.status', read_only=True)
    order_date = serializers.DateTimeField(source='order.created_at', format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order_id', 'product_name', 'quantity', 'product_price', 
            'customer_name', 'address', 'status', 'order_date'
        ]

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class ReviewSerializer(serializers.ModelSerializer):
   
    user_name = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'comment', 'created_at_formatted']

    def get_user_name(self, obj):
        
        first = obj.user.first_name
        last = obj.user.last_name
        
        full_name = f"{first} {last}".strip()
        
        if full_name:
            return full_name
        return "Verified Customer"

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y")