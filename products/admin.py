from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "quantity", "in_stock", "created_at")
    list_editable = ("price", "quantity")
    search_fields = ("name", "description")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
