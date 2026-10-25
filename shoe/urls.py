from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('cart/', views.cart, name='cart'),
    path('category/<slug:category_slug>/', views.category_view, name='category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    path('payment/success/<str:order_number>/', views.payment_success, name='payment_success'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
]
