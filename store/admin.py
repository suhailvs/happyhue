import csv

from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Category, Product,ProductImage, Order, OrderItem, Payment

STATUS_COLORS = {
    "pending": "#8a6d00", "paid": "#0f7b63", "failed": "#c8445f", "cancelled": "#6b7280",
    "shipped": "#2a3bd0", "delivered": "#0f7b63", "refunded": "#6b7280",
}
def _thumb(image, size=48):
    if not image:
        return "-"
    return format_html(
        '<img src="{}" alt="" style="width:{}px;height:{}px;object-fit:cover;border-radius:6px">',
        image.url, size, size,
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ("preview", "image", "alt", "sort_order")
    readonly_fields = ("preview",)

    @admin.display(description="Preview")
    def preview(self, obj):
        return _thumb(obj.image, 72) if obj.pk else "-"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "parent", "slug", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("parent", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumb", "name", "category", "brand", "price", "stock", "home_tab", "is_active")
    list_display_links = ("thumb", "name")
    list_editable = ("price", "stock", "is_active")
    list_filter = ("category", "is_active", "home_tab", "badge")
    search_fields = ("name", "brand", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category",)
    inlines = [ProductImageInline]
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "brand", "description")}),
        ("Pricing and stock", {"fields": ("price", "compare_at_price", "badge", "stock")}),
        ("Storefront", {"fields": ("home_tab", "sort_order", "is_active")}),
        ("Fallback illustration", {
            "classes": ("collapse",),
            "description": "Shown on cards when a product has no photos.",
            "fields": ("icon", "colors"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("images")

    @admin.display(description="Image")
    def thumb(self, obj):
        main = obj.main_image
        return _thumb(main.image if main else None)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "brand", "unit_price", "quantity", "line_total", "options")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Line total")
    def line_total(self, obj):
        return obj.line_total


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("razorpay_order_id", "razorpay_payment_id", "amount", "status", "method", "error", "created_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "full_name", "phone", "status_badge", "total", "item_count", "created_at", "paid_at")
    list_filter = ("status", "state", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone", "user__phone", "payments__razorpay_payment_id")
    date_hierarchy = "created_at"
    list_per_page = 50
    inlines = [OrderItemInline, PaymentInline]
    actions = ["mark_shipped", "mark_delivered", "export_csv"]
    fieldsets = (
        ("Order", {"fields": ("order_number", "status", "created_at", "paid_at")}),
        ("Customer", {"fields": ("user", "full_name", "email", "phone")}),
        ("Delivery address", {"fields": ("address_line1", "address_line2", "city", "state", "pincode", "notes")}),
        ("Amounts", {"fields": ("subtotal", "shipping_fee", "total")}),
    )
    # Money and customer details are a record of what happened; staff only move the status along.
    readonly_fields = (
        "order_number", "created_at", "paid_at", "user", "full_name", "email", "phone", "address_line1", "address_line2",
        "city", "state", "pincode", "notes", "subtotal", "shipping_fee", "total",
    )

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user").prefetch_related("items")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<b style="color:{}">{}</b>', STATUS_COLORS.get(obj.status, "inherit"), obj.get_status_display()
        )

    @admin.display(description="Items")
    def item_count(self, obj):
        return sum(i.quantity for i in obj.items.all())

    def _move(self, request, queryset, allowed_from, to, label):
        updated = queryset.filter(status__in=allowed_from).update(status=to)
        skipped = queryset.count() - updated
        self.message_user(request, f"{updated} order(s) marked {label}.", messages.SUCCESS)
        if skipped:
            self.message_user(
                request, f"{skipped} skipped: only {', '.join(allowed_from)} orders can be marked {label}.", messages.WARNING
            )

    @admin.action(description="Mark selected paid orders as shipped")
    def mark_shipped(self, request, queryset):
        self._move(request, queryset, [Order.Status.PAID], Order.Status.SHIPPED, "shipped")

    @admin.action(description="Mark selected shipped orders as delivered")
    def mark_delivered(self, request, queryset):
        self._move(request, queryset, [Order.Status.SHIPPED], Order.Status.DELIVERED, "delivered")

    @admin.action(description="Export selected orders to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        w = csv.writer(response)
        w.writerow(["Order", "Date", "Status", "Name", "Email", "Phone", "Address", "City", "State", "PIN", "Items", "Total"])
        for o in queryset.prefetch_related("items"):
            address = ", ".join(x for x in (o.address_line1, o.address_line2) if x)
            items = "; ".join(f"{i.quantity} x {i.name}" for i in o.items.all())
            w.writerow([o.order_number, o.created_at.strftime("%Y-%m-%d %H:%M"),
                        o.get_status_display(), o.full_name, o.email, o.phone, address, o.city, o.state, o.pincode, items, o.total])
        return response


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("razorpay_order_id", "razorpay_payment_id", "order", "amount_rupees", "status", "method", "created_at")
    list_filter = ("status", "method")
    search_fields = ("razorpay_order_id", "razorpay_payment_id", "order__order_number")
    readonly_fields = [f.name for f in Payment._meta.fields]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Amount")
    def amount_rupees(self, obj):
        return f"₹{obj.amount / 100:,.2f}"
