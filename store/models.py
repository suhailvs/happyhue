from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal

from django.utils import timezone
from django.utils.crypto import get_random_string


def split_colors(value):
    return [c.strip() for c in value.split(",") if c.strip()]


class Category(models.Model):
    """A top-level category (Art materials, Handmade, Art framing) or a sub-category."""

    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    blurb = models.CharField(
        max_length=160, blank=True, help_text="One line shown on category tiles and at the top of the list page."
    )
    menu_blurb = models.CharField(
        max_length=120, blank=True, help_text="Shorter line for the mega menu. Falls back to the blurb."
    )
    icon = models.CharField(
        max_length=40, default="a-tube",
        help_text="Illustration id from templates/partials/sprite.html, for example a-tube.",
    )
    colors = models.CharField(
        max_length=60, default="#BA3521,#8A98A3,#CDBF9B", help_text="Up to three hex colors, comma separated."
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return f"{self.parent.name} / {self.name}" if self.parent_id else self.name

    def get_absolute_url(self):
        return reverse("store:category", args=[self.slug])

    @property
    def c(self):
        return split_colors(self.colors)

    def subtree_ids(self):
        """This category's id plus the ids of everything below it."""
        ids = [self.pk]
        frontier = [self.pk]
        while frontier:
            frontier = list(Category.objects.filter(parent_id__in=frontier).values_list("pk", flat=True))
            ids += frontier
        return ids


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, category__is_active=True)


class Product(models.Model):
    class HomeTab(models.TextChoices):
        NONE = "", "Not on the homepage"
        BEST = "best", "Bestsellers"
        NEW = "new", "New arrivals"
        HAND = "hand", "Handmade picks"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    brand = models.CharField(max_length=80, help_text="Brand, or the maker for handmade pieces.")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Original price. Shown struck through next to the sale price.",
    )
    badge = models.CharField(max_length=20, blank=True, help_text="For example New, Sale or Bestseller.")
    stock = models.PositiveIntegerField(default=0)
    icon = models.CharField(
        max_length=40, default="a-tube", help_text="Illustration id from templates/partials/sprite.html."
    )
    colors = models.CharField(
        max_length=60, default="#BA3521,#8A98A3,#CDBF9B", help_text="Up to three hex colors, comma separated."
    )
    home_tab = models.CharField(max_length=8, choices=HomeTab.choices, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0, help_text="Lower numbers come first in Featured order.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200] or "product"
            slug, n = base, 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    # Names the templates and the product card partial already use.
    @property
    def by(self):
        return self.brand

    @property
    def c(self):
        return split_colors(self.colors)

    @property
    def old_price(self):
        return self.compare_at_price

    @property
    def in_stock(self):
        return self.stock > 0






def new_order_number():
    return "HH" + get_random_string(8, "ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting payment"
        PAID = "paid", "Paid"
        FAILED = "failed", "Payment failed"
        CANCELLED = "cancelled", "Cancelled"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        REFUNDED = "refunded", "Refunded"

    order_number = models.CharField(max_length=12, unique=True, default=new_order_number, editable=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=6)
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()})"

    @property
    def total_paise(self):
        return int((self.total * 100).to_integral_value())

    @property
    def is_paid(self):
        return self.paid_at is not None


class OrderItem(models.Model):
    """A line on an order. Name and price are copied so later catalog edits don't change old orders."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items")
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=80, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)
    options = models.JSONField(default=dict, blank=True, help_text="Custom framing choices, empty for catalog products.")

    def __str__(self):
        return f"{self.quantity} x {self.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    razorpay_order_id = models.CharField(max_length=40, unique=True)
    razorpay_payment_id = models.CharField(max_length=40, blank=True, db_index=True)
    razorpay_signature = models.CharField(max_length=128, blank=True)
    amount = models.PositiveIntegerField(help_text="In paise.")
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)
    method = models.CharField(max_length=30, blank=True)
    error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.razorpay_order_id} ({self.status})"
