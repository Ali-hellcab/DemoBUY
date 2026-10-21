from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:product_id>/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    
    # Checkout and Order Management
    path("checkout/", views.checkout, name="checkout"),
    path("payment/verify/", views.verify_payment, name="verify_payment"),
    path("payment/webhook/", views.paystack_webhook, name="paystack_webhook"),
    path("history/", views.order_history, name="order_history"),
]