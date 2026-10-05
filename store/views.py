from django.shortcuts import render

from . import data


def home(request):
    categories = {c["slug"]: c for c in data.CATEGORIES}
    tabs = [
        {"key": key, "label": label, "products": [data.PRODUCTS[pid] for pid in ids]}
        for key, label, ids in data.PRODUCT_TABS
    ]
    context = {
        "materials": categories["art-materials"],
        "handmade": categories["handmade"],
        "framing": categories["art-framing"],
        "tabs": tabs,
        "brands": data.BRANDS,
        "why_us": data.WHY_US,
        "posts": data.POSTS,
        "frame_builder": data.FRAME_BUILDER,
    }
    return render(request, "home.html", context)
