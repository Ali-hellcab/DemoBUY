import hmac
import hashlib
import json
import requests
import uuid
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .models import Product, Order, OrderItem

def home(request):
    products = Product.objects.all()

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query))

    price_filter = request.GET.get("price", "")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if price_filter == "under_5000":
        products = products.filter(price__lt=5000)
    elif price_filter == "over_5000":
        products = products.filter(price__gt=5000)
    elif price_filter == "5000_10000":
        products = products.filter(price__gte=5000, price__lte=10000)
    elif min_price or max_price:
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)

    context = {
        "products": products,
        "query": query,
        "price_filter": price_filter,
        "min_price": min_price or "",
        "max_price": max_price or "",
    }
    return render(request, "products/home.html", context)


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)

    if product.quantity <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect(request.META.get("HTTP_REFERER", "home"))

    quantity = int(request.POST.get("quantity", 1))
    cart.add(product=product, quantity=quantity)
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@require_POST
def update_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 1))

    if quantity <= 0:
        cart.remove(product)
        messages.info(request, f"Removed {product.name} from your cart.")
    else:
        cart.add(product=product, quantity=quantity, override_quantity=True)
        messages.success(request, "Cart updated.")
    return redirect("cart")


@require_POST
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.info(request, f"Removed {product.name} from your cart.")
    return redirect("cart")


def cart_detail(request):
    cart = Cart(request)
    
    # Add this block to handle the clear action directly on the cart page
    if request.method == "POST" and "clear_cart" in request.POST:
        cart.clear()
        messages.info(request, "Your cart has been completely cleared.")
        return redirect("cart")
        
    return render(request, "products/cart.html", {"cart": cart})


@login_required
@require_POST
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    items = list(cart)
    # 1. Validate stock before proceeding
    for item in items:
        product = item["product"]
        if item["quantity"] > product.quantity:
            messages.error(
                request,
                f"Sorry, only {product.quantity} unit(s) of {product.name} are left. Please update your cart."
            )
            return redirect("cart")

    total = cart.get_total_price()
    reference = str(uuid.uuid4())

    # 2. Create the Order in the database
    order = Order.objects.create(
        user=request.user,
        total_amount=total,
        paystack_reference=reference
    )
    
    for item in items:
        OrderItem.objects.create(
            order=order, 
            product=item["product"], 
            quantity=item["quantity"], 
            price=item["product"].price  # Fixed: correctly pulls price from the Product model
        )

    # 3. Initialize Paystack
    callback_url = request.build_absolute_uri(reverse("verify_payment"))
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": request.user.email,
        "amount": int(total * 100),  # Convert Naira to Kobo
        "reference": reference,
        "callback_url": callback_url
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    res_data = response.json()

    if res_data.get("status"):
        return redirect(res_data["data"]["authorization_url"])
    else:
        messages.error(request, f"Payment initialization failed: {res_data.get('message')}")
        return redirect("cart")


@login_required
def verify_payment(request):
    reference = request.GET.get("reference")
    if not reference:
        messages.error(request, "No transaction reference found.")
        return redirect("cart")

    order = get_object_or_404(Order, paystack_reference=reference, user=request.user)

    if order.is_paid:
        messages.info(request, "This order has already been paid for.")
        return redirect("home")

    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    res_data = response.json()

    if res_data.get("status") and res_data["data"]["status"] == "success":
        is_test_transaction = res_data["data"].get("domain") == "test"

        with transaction.atomic():
            for item in order.items.all():
                locked_product = Product.objects.select_for_update().get(id=item.product.id)
                if locked_product.quantity >= item.quantity:
                    locked_product.quantity -= item.quantity
                    locked_product.save()

        order.is_paid = True
        order.payment_status = "Successful"
        order.is_demo_payment = is_test_transaction
        order.save()
        
        Cart(request).clear()
        
        messages.success(request, f"Payment successful! Your order (Ref: {reference[:8]}) has been placed.")
        return redirect("home")  # Redirects to home page on success
    else:
        messages.error(request, "Payment failed or was canceled. Please try again.")
        return redirect("cart")


@csrf_exempt
@require_POST
def paystack_webhook(request):
    paystack_signature = request.headers.get("x-paystack-signature")
    if not paystack_signature:
        return HttpResponse(status=400)

    secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    body = request.body
    computed_hmac = hmac.new(secret, body, hashlib.sha512).hexdigest()

    if computed_hmac != paystack_signature:
        return HttpResponse(status=400)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event = payload.get("event")
    data = payload.get("data", {})

    if event == "charge.success":
        reference = data.get("reference")
        is_test_transaction = data.get("domain") == "test"
        
        try:
            order = Order.objects.get(paystack_reference=reference)
            
            if not order.is_paid:
                with transaction.atomic():
                    for item in order.items.all():
                        locked_product = Product.objects.select_for_update().get(id=item.product.id)
                        if locked_product.quantity >= item.quantity:
                            locked_product.quantity -= item.quantity
                            locked_product.save()
                    
                    order.is_paid = True
                    order.payment_status = "Successful"
                    order.is_demo_payment = is_test_transaction
                    order.save()
                    
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'products/order_history.html', {'orders': orders})


