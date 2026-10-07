from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import Category, Product
from .navigation import get_navigation

from . import data



PAGE_SIZE = 12
SORTS = {
    "featured": ("Featured", ("sort_order", "id")),
    "newest": ("Newest", ("-created_at", "-id")),
    "price_asc": ("Price, low to high", ("price", "id")),
    "price_desc": ("Price, high to low", ("-price", "id")),
}

def home(request):
    sections = {c["slug"]: c for c in get_navigation(request)}
    tabs = [
        {"key": key, "label": label, "products": Product.objects.active().filter(home_tab=key)[:4]}
        for key, label in Product.HomeTab.choices
        if key
    ]
    context = {
        "materials": sections.get("art-materials"),
        "handmade": sections.get("handmade"),
        "framing": sections.get("art-framing"),
        "tabs": tabs,
        "brands": data.BRANDS,
        "why_us": data.WHY_US,
        "posts": data.POSTS,
        "frame_builder": data.FRAME_BUILDER,
    }
    return render(request, "home.html", context)



def category(request, slug):
    category = get_object_or_404(Category.objects.select_related("parent"), slug=slug, is_active=True)
    # Sub-categories show their siblings as pills; top-level categories show their children.
    pills_root = category.parent or category
    subcategories = pills_root.children.filter(is_active=True)

    sort = request.GET.get("sort", "featured")
    if sort not in SORTS:
        sort = "featured"
    products = (
        Product.objects.active()
        .filter(category__in=category.subtree_ids())
        .order_by(*SORTS[sort][1])
    )
    page_obj = Paginator(products, PAGE_SIZE).get_page(request.GET.get("page"))

    # Framing is made to measure, so its category points at the builder instead of a product grid.
    cta_href = next((c.get("cta_href") for c in data.CATEGORIES if c["slug"] == pills_root.slug), "")
    context = {
        "category": category,
        "pills_root": pills_root,
        "subcategories": subcategories,
        "page_obj": page_obj,
        "sort": sort,
        "sorts": [(key, label) for key, (label, _) in SORTS.items()],
        "builder_url": reverse("store:home") + cta_href if cta_href else "",
    }
    return render(request, "category.html", context)