from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Category, Shop, Product, Order, OrderItem
from .serializers import CategorySerializer, ShopSerializer, ProductSerializer, UserSerializer, OrderSerializer, OrderItemSerializer
from .models import UserProfile # Add this to your imports!
from .models import Address
from .serializers import AddressSerializer


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
            # NEW: Get the address text sent from the frontend
            selected_address_text = request.data.get('address_text', "")

            if not item_ids:
                return Response({"error": "No items selected."}, status=status.HTTP_400_BAD_REQUEST)

            items_to_checkout = active_order.items.filter(id__in=item_ids)

            # Scenario A: Full Checkout
            if items_to_checkout.count() == active_order.items.count():
                active_order.is_completed = True
                active_order.address_text = selected_address_text # Save address
                active_order.status = 'Pending'
                active_order.save()
            
            # Scenario B: Partial Checkout
            else:
                new_order = Order.objects.create(
                    user=request.user, 
                    is_completed=True, 
                    address_text=selected_address_text, # Save address
                    status='Pending'
                )
                for item in items_to_checkout:
                    item.order = new_order
                    item.save()

            return Response({"message": "Order placed successfully!"}, status=status.HTTP_200_OK)

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
            address = Address.objects.get(pk=pk, user=request.user)
            was_default = address.is_default
            address.delete()

            if was_default:
                next_addr = Address.objects.filter(user=request.user).first()
                if next_addr:
                    next_addr.is_default = True
                    next_addr.save()

            return Response({"message": "Address deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)
        
class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user, is_completed=True).order_by('created_at')
        
        # We can reuse your existing OrderSerializer or make a detailed one
        data = []
        for order in orders:
            items = []
            for item in order.items.all():
                items.append({
                    "title": item.product.title,
                    "quantity": item.quantity,
                    "price": float(item.product.price)
                })
            
            data.append({
                "id": order.id,
                "status": order.status,
                "date": order.created_at.strftime("%b %d, %Y"),
                "total": sum(i['price'] * i['quantity'] for i in items) + 50, # Items + Delivery Fee
                "items": items
            })
            
        return Response(data)