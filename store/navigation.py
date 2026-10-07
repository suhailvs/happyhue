from django.db.models import Count, Prefetch, Q

from . import data
from .models import Category


def _count_label(n):
    return f"{n} item{'s' if n != 1 else ''}" if n else ""


def build_navigation():
    children = (
        Category.objects.filter(is_active=True)
        .annotate(product_count=Count("products", filter=Q(products__is_active=True)))
        .order_by("sort_order", "name")
    )
    top_level = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related(Prefetch("children", queryset=children))
        .order_by("sort_order", "name")
    )
    presentation = {
        c["slug"]: {k: v for k, v in c.items() if k != "children"} for c in data.CATEGORIES
    }
    nav = []
    for top in top_level:
        nav.append({
            **presentation.get(top.slug, {}),
            "slug": top.slug,
            "name": top.name,
            "url": top.get_absolute_url(),
            "children": [
                {
                    "slug": kid.slug,
                    "name": kid.name,
                    "url": kid.get_absolute_url(),
                    "blurb": kid.blurb,
                    "menu_blurb": kid.menu_blurb or kid.blurb,
                    "count_label": _count_label(kid.product_count),
                    "icon": kid.icon,
                    "c": kid.c,
                }
                for kid in top.children.all()
            ],
        })
    return nav


def get_navigation(request):
    """Build once per request; the context processor and the view share it."""
    if not hasattr(request, "_store_navigation"):
        request._store_navigation = build_navigation()
    return request._store_navigation