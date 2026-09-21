from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .models import Product


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
    return render(request, "products/cart.html", {"cart": cart})


@login_required
@require_POST
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    # Validate stock for every item before touching the database
    items = list(cart)
    for item in items:
        product = item["product"]
        if item["quantity"] > product.quantity:
            messages.error(
                request,
                f"Sorry, only {product.quantity} unit(s) of {product.name} are left in stock. "
                f"Please update your cart.",
            )
            return redirect("cart")

    # Deduct stock atomically
    message_parts = []
    with transaction.atomic():
        for item in items:
            product = item["product"]
            locked_product = Product.objects.select_for_update().get(id=product.id)
            if item["quantity"] > locked_product.quantity:
                messages.error(
                    request,
                    f"Sorry, {product.name} no longer has enough stock. Please update your cart.",
                )
                return redirect("cart")
            locked_product.quantity -= item["quantity"]
            locked_product.save()
            message_parts.append(f"{product.name} x{item['quantity']}")

    total = cart.get_total_price()
    cart.clear()

    whatsapp_text = f"I want to buy: {', '.join(message_parts)}. Total: ₦{total}"
    whatsapp_url = f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(whatsapp_text)}"

    return redirect(whatsapp_url)
