from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from store import data
from store.models import Category, Product


class Command(BaseCommand):
    help = "Create or update categories and products from store/data.py. Safe to run more than once."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for order, top in enumerate(data.CATEGORIES):
            first = top["children"][0]
            root, _ = Category.objects.update_or_create(
                slug=top["slug"],
                defaults={
                    "parent": None, "name": top["name"], "blurb": top["tagline"], "icon": first["icon"],
                    "colors": ",".join(first["c"]), "sort_order": order, "is_active": True,
                },
            )
            categories[root.slug] = root
            for child_order, child in enumerate(top["children"]):
                kid, _ = Category.objects.update_or_create(
                    slug=child["slug"],
                    defaults={
                        "parent": root, "name": child["name"], "blurb": child["blurb"],
                        "menu_blurb": child.get("menu_blurb", ""), "icon": child["icon"],
                        "colors": ",".join(child["c"]), "sort_order": child_order, "is_active": True,
                    },
                )
                categories[kid.slug] = kid

        tab_for = {pid: (key, pos) for key, _label, ids in data.PRODUCT_TABS for pos, pid in enumerate(ids)}
        for pid, p in data.PRODUCTS.items():
            tab, pos = tab_for.get(pid, ("", 0))
            Product.objects.update_or_create(
                slug=slugify(p["name"])[:200],
                defaults={
                    "category": categories[p["category"]], "name": p["name"], "brand": p["by"],
                    "price": p["price"], "compare_at_price": p.get("old_price"),
                    "badge": p.get("badge", ""), "stock": p.get("stock", 25), "icon": p["icon"],
                    "colors": ",".join(p["c"]), "home_tab": tab, "sort_order": pos, "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS(
            f"{Category.objects.count()} categories, {Product.objects.count()} products."
        ))
