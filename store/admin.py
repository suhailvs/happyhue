from django.contrib import admin

from .models import Category, Product, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "name", "brand", "unit_price", "quantity", "options")
    can_delete = False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("razorpay_order_id", "razorpay_payment_id", "amount", "status", "method", "error", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "full_name", "status", "total", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone")
    readonly_fields = ("order_number", "subtotal", "shipping_fee", "total", "created_at", "paid_at")
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("razorpay_order_id", "razorpay_payment_id", "order", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("razorpay_order_id", "razorpay_payment_id", "order__order_number")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "slug", "sort_order", "is_active")
    list_filter = ("parent", "is_active")
    list_select_related = ("parent",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "price", "stock", "home_tab", "is_active")
    list_editable = ("price", "stock", "is_active")
    list_filter = ("category", "home_tab", "is_active")
    list_select_related = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "brand")