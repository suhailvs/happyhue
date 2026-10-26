from django.core.management.base import BaseCommand
from django.db import transaction
from store import data
from store.models import Category


class Command(BaseCommand):
    help = "Create or update categories from store/data.py. Safe to run more than once."

    @transaction.atomic
    def handle(self, *args, **options):
        for order, top in enumerate(data.CATEGORIES):
            first = top["children"][0]
            root, _ = Category.objects.update_or_create(
                slug=top["slug"],
                defaults={
                    "parent": None, "name": top["name"], "blurb": top["tagline"], "icon": first["icon"],
                    "colors": ",".join(first["c"]), "sort_order": order, "is_active": True,
                },
            )
            for child_order, child in enumerate(top["children"]):
                Category.objects.update_or_create(
                    slug=child["slug"],
                    defaults={
                        "parent": root, "name": child["name"], "blurb": child["blurb"],
                        "menu_blurb": child.get("menu_blurb", ""), "icon": child["icon"],
                        "colors": ",".join(child["c"]), "sort_order": child_order, "is_active": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS(
            f"{Category.objects.count()} categories."
        ))
