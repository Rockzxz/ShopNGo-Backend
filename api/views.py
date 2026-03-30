from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    Category, Shop, Product, Order, OrderItem, 
    Wishlist, Review, UserProfile, Address
)
from .serializers import (
    CategorySerializer, ShopSerializer, ProductSerializer, 
    UserSerializer, OrderSerializer, OrderItemSerializer,
    ReviewSerializer, AddressSerializer, WishlistSerializer,
    AdminCreateMerchantSerializer, MerchantOrderItemSerializer, 
    OrderStatusUpdateSerializer
)



class RegisterView(APIView):
    def post(self, request):
        # --- ADD THIS PRINT STATEMENT ---
        print("🚨 INCOMING DATA FROM APP:", request.data)
        # --------------------------------
        
        data = request.data.copy()
        data['username'] = data.get('email') 
        
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            
            name = request.data.get('first_name', '')
            if name:
                user.first_name = name
                user.save()
            
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(username=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer

    # We change this to a dynamic query instead of just returning ALL products
    def get_queryset(self):
        queryset = Product.objects.all()
        # Look for a '?category_id=' in the URL sent from React Native
        category_id = self.request.query_params.get('category_id', None)
        
        if category_id is not None:
            # If the app asks for a specific category, filter the list!
            queryset = queryset.filter(category_id=category_id)
            
        return queryset

class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ShopList(generics.ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # Make sure this says 'def get', NOT 'def post'!
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class CartView(APIView):
    permission_classes = [IsAuthenticated] # Only logged-in users get a cart!

    def get(self, request):
        order, created = Order.objects.get_or_create(user=request.user, is_completed=False)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    # api/views.py

    def post(self, request):
        order, created = Order.objects.get_or_create(user=request.user, is_completed=False)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        order_item, item_created = OrderItem.objects.get_or_create(order=order, product=product)
        if not item_created:
            order_item.quantity += quantity 
        else:
            order_item.quantity = quantity 
        order_item.save()

        # CHANGE THIS: Return the OrderItemSerializer instead of OrderSerializer
        serializer = OrderItemSerializer(order_item) 
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
# api/views.py

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            active_order = Order.objects.get(user=request.user, is_completed=False)
            item_ids = request.data.get('item_ids', [])
            selected_address_text = request.data.get('address_text', "No Address Provided")

            if not item_ids:
                return Response({"error": "No items selected."}, status=status.HTTP_400_BAD_REQUEST)

            items_to_checkout = active_order.items.filter(id__in=item_ids)
            order_id = None

            # Scenario A: Full Checkout
            if items_to_checkout.count() == active_order.items.count():
                active_order.is_completed = True
                active_order.address_text = selected_address_text
                active_order.status = 'Pending'
                active_order.save()
                order_id = active_order.id
            
            # Scenario B: Partial Checkout (User only selected some items in cart)
            else:
                new_order = Order.objects.create(
                    user=request.user, 
                    is_completed=True, 
                    address_text=selected_address_text, 
                    status='Pending'
                )
                for item in items_to_checkout:
                    item.order = new_order
                    item.save()
                order_id = new_order.id

            return Response({
                "message": "Order placed successfully!",
                "order_id": order_id  # 🚨 This is what the Success Screen needs
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({"error": "No active cart."}, status=status.HTTP_404_NOT_FOUND)
        
class AddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Find the profile or create a blank one if they don't have one yet
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            "first_name": request.user.first_name,
            "phone_number": profile.phone_number or "",
            "address": profile.address or ""
        })

    def put(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.address = request.data.get('address', profile.address)
        profile.phone_number = request.data.get('phone_number', profile.phone_number)
        profile.save()
        
        return Response({"message": "Address updated successfully!"}, status=status.HTTP_200_OK)
    
class AddressListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all addresses for this user, putting the default one at the very top
        addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id')
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        # If they check "Make Default", or if this is their very first address, we make it the default!
        set_default = request.data.get('is_default', False)
        
        if set_default or not Address.objects.filter(user=request.user).exists():
            # Turn off 'is_default' for all their other addresses first
            Address.objects.filter(user=request.user).update(is_default=False)
            set_default = True

        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, is_default=set_default)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # Look for the address specifically belonging to the logged-in user
            address = Address.objects.get(pk=pk, user=request.user)
            was_default = address.is_default
            address.delete()

            # If they deleted their default address, set a new one automatically
            if was_default:
                next_addr = Address.objects.filter(user=request.user).first()
                if next_addr:
                    next_addr.is_default = True
                    next_addr.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)
        
class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user, is_completed=True).order_by('-created_at')
        data = []
        for order in orders:
            items = []
            for item in order.items.all():
                items.append({
                    "id": item.product.id,
                    "title": item.product.title,
                    "quantity": item.quantity,
                    "price": float(item.product.price),
                    "shop": item.product.shop.name,
                    "shop_id": item.product.shop.id, 
                })
            
            data.append({
                "id": order.id,
                "status": order.status,
                "date": order.created_at.strftime("%b %d, %Y"),
                "address_text": order.address_text, # Ensure this is passed to the app
                "total": sum(i['price'] * i['quantity'] for i in items) + 50, # Items + Delivery Fee
                "items": items
            })
            
        return Response(data)
    
class WishlistView(APIView):
    permission_classes = [IsAuthenticated] # User MUST be logged in

    def get(self, request):
        # 1. Get all wishlist items for this specific user
        wishlist_items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist_items, many=True)
        
        # 2. Clean the data: Extract JUST the product objects
        # This makes it perfectly match your React Native frontend structure!
        products = [item['product'] for item in serializer.data]
        
        return Response(products, status=status.HTTP_200_OK)

    def post(self, request):
        # 1. Get the product ID sent from React Native
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Find the product in the database
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # 3. Check if this product is ALREADY in the user's wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            # If it exists, TOGGLE IT OFF (Delete it)
            wishlist_item.delete()
            return Response({"message": "Removed from wishlist", "added": False}, status=status.HTTP_200_OK)
        else:
            # If it doesn't exist, TOGGLE IT ON (Create it)
            Wishlist.objects.create(user=request.user, product=product)
            return Response({"message": "Added to wishlist", "added": True}, status=status.HTTP_201_CREATED)
        
class AdminCreateMerchantView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = AdminCreateMerchantSerializer

class AdminMerchantListView(generics.ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]

from rest_framework.exceptions import ValidationError

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        # Filters products so merchants only see their own items
        return Product.objects.filter(shop__user=self.request.user)

    def perform_create(self, serializer):
        # SAFETY CHECK: Ensure the user actually has a shop profile
        try:
            merchant_shop = self.request.user.shop
            if merchant_shop is None:
                raise ValidationError({"detail": "You do not have a merchant shop profile linked to this account."})
            
            # Attach the shop and save the product
            serializer.save(shop=merchant_shop)
        except AttributeError:
            raise ValidationError({"detail": "This user account is not registered as a Merchant."})

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(shop__user=self.request.user)

class MerchantProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.shop

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
class MerchantOrderListView(generics.ListAPIView):
    serializer_class = MerchantOrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(
            product__shop__user=self.request.user,
            order__is_completed=True
        ).order_by('-order__created_at')

class MerchantOrderStatusUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.data.get('status')
        old_status = order.status

        # 🚨 TRIGGER: Deduct stock when item leaves the shop
        if new_status in ['Out for Delivery', 'Delivered'] and old_status not in ['Out for Delivery', 'Delivered']:
            for item in order.items.all():  # Uses the 'items' related_name
                product = item.product
                if product.stock_quantity >= item.quantity:
                    product.stock_quantity -= item.quantity
                    product.save()
                else:
                    return Response(
                        {"error": f"Insufficient stock for {product.title}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

        return super().patch(request, *args, **kwargs)
    
class ProductReviewView(APIView):
    # This allows public GET but protected POST
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, product_id):
        reviews = Review.objects.filter(product_id=product_id).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, product_id):
        user = request.user
        
        # 🚨 VERIFICATION: Check if user has a 'Confirmed' order for this specific product
        has_purchased = OrderItem.objects.filter(
            order__user=user,
            product_id=product_id,
            order__status='Confirmed'
        ).exists()

        if not has_purchased:
            return Response(
                {"error": "You must purchase and receive this item before leaving a review."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent duplicate reviews
        if Review.objects.filter(user=user, product_id=product_id).exists():
            return Response(
                {"error": "You have already reviewed this product."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user, product_id=product_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ShopDetailView(generics.RetrieveAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]