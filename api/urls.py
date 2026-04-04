from django.urls import path
from . import views

urlpatterns = [
    # --- AUTH & USER ---
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # --- CATALOG & REVIEWS ---
    path('products/', views.ProductList.as_view(), name='product-list'),
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('shops/', views.ShopList.as_view(), name='shop-list'),
    path('shops/<int:pk>/', views.ShopDetailView.as_view(), name='shop-detail'),
    path('products/<int:product_id>/reviews/', views.ProductReviewView.as_view(), name='product-reviews'),

    # --- SHOPPING & CHECKOUT ---
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('address/', views.AddressView.as_view(), name='address'),
    path('addresses/', views.AddressListView.as_view(), name='addresses'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('orders/', views.OrderHistoryView.as_view(), name='order-history'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),

    # --- ADMIN ENDPOINTS ---
    path('admin/create-merchant/', views.AdminCreateMerchantView.as_view(), name='create-merchant'),
    path('admin/merchants/', views.AdminMerchantListView.as_view(), name='admin-merchant-list'), 

    # --- MERCHANT ENDPOINTS ---
    path('merchant/profile/', views.MerchantProfileDetailView.as_view(), name='merchant-profile'),
    path('merchant/products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('merchant/products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('merchant/orders/', views.MerchantOrderListView.as_view(), name='merchant-orders'),
    path('merchant/orders/<int:pk>/status/', views.MerchantOrderStatusUpdateView.as_view(), name='merchant-order-status'),
]