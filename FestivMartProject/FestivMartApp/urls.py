from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='home'),
    path('seasonal/', views.seasonal_mart, name='seasonal'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('shop/', views.shop, name='shop'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('score/', views.score_view, name='score'),
    path('add-product/', views.add_product, name='add_product'),
    path('api/dates/', views.year_dates_api, name='year_dates_api'),
    path('api/product/<int:product_id>/', views.product_detail_api, name='product_detail_api'),
    
    # Cart API endpoints
    path('api/cart/add/', views.cart_add, name='cart_add'),
    path('api/cart/update/', views.cart_update, name='cart_update'),
    path('api/cart/remove/', views.cart_remove, name='cart_remove'),
    path('api/cart/coupon/', views.cart_apply_coupon, name='cart_apply_coupon'),
    path('api/cart/data/', views.cart_data, name='cart_data'),
    
    # Order
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
]

