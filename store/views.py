from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import FramingQuoteForm
from django.db.models import Prefetch
from .models import Banner, Category, Product
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
        "quote_sizes": data.QUOTE_SIZES,
        "banners": Banner.objects.filter(is_active=True).select_related("category"),
    }
    return render(request, "home.html", context)



def category(request, slug):
    category = get_object_or_404(Category.objects.select_related("parent"), slug=slug, is_active=True)
    # Sub-categories show their siblings as pills; top-level categories show their children.
    # Walk up to the top-level category (e.g. Art Materials) so the sidebar
    # shows the full tree whichever level the visitor is on.
    root = category
    while root.parent_id:
        root = root.parent

    sidebar_groups = (
        root.children.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=Category.objects.filter(is_active=True),
                to_attr="active_children",
            )
        )
    )

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
    cta_href = next((c.get("cta_href") for c in data.CATEGORIES if c["slug"] == root.slug), "")
    context = {
        "category": category,
        "pills_root": root,
        "page_obj": page_obj,
        "sort": sort,
        "sorts": [(key, label) for key, (label, _) in SORTS.items()],
        "builder_url": reverse("store:home") + cta_href if cta_href else "",
        "sidebar_groups": sidebar_groups,
    }
    return render(request, "category.html", context)

@require_POST
def framing_quote(request):
    form = FramingQuoteForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thanks! We have your request and will contact you soon.")
    else:
        messages.error(request, "Please fill in your name and phone or email.")
    return redirect(reverse("store:home") + "#framing")

# pressman ajax
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
@csrf_exempt
def ajax_pressman_lat_lng(request):
    import requests
    data = json.loads(request.body)
    url = data.get("url", "").strip()
    print(url,'url')
    if url:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
            url = resp.url
        except requests.RequestException:
            try:
                resp = requests.get(url, allow_redirects=True, timeout=5)
                url = resp.url
            except requests.RequestException:
                pass
    return JsonResponse({"url":url})
