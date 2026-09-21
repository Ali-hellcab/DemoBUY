from .cart import Cart


def cart_summary(request):
    cart = Cart(request)
    return {
        "cart_item_count": cart.get_item_count(),
        "cart_total_price": cart.get_total_price(),
    }
