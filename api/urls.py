from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('products/', views.ProductList.as_view(), name='product-list'),
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('shops/', views.ShopList.as_view(), name='shop-list'),
    # Add this line to your urlpatterns:
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('cart/', views.CartView.as_view(), name='cart'),
    # Add this right below your cart/ path:
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('address/', views.AddressView.as_view(), name='address'),
    path('addresses/', views.AddressListView.as_view(), name='addresses'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('orders/', views.OrderHistoryView.as_view(), name='order-history'),
]