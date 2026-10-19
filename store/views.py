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

# Home page banner slides. Images live in store/static/images/.
BANNERS = [
    {"img": "images/banner-1.jpg", "title": "Colour for your walls and your studio",
     "text": "Art materials, handmade pieces and custom framing.", "cta": "Shop art materials", "slug": "art-materials"},
    {"img": "images/banner-2.jpg", "title": "Original watercolours",
     "text": "Painted by hand and signed by the artist.", "cta": "View paintings", "slug": "paintings-original"},
    {"img": "images/banner-3.jpg", "title": "Everything for the first wash",
     "text": "Paints, brushes and papers from brands we trust.", "cta": "Shop now", "slug": "art-materials"},
]


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
        "why_us": data.WHY_US,
        "quote_sizes": data.QUOTE_SIZES,
        "banners": [{**b, "url": reverse("store:category", args=[b["slug"]])} for b in BANNERS],
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
