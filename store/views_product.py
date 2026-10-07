from django.shortcuts import get_object_or_404, render

from .models import Product


def product(request, slug):
    item = get_object_or_404(Product.objects.active().select_related("category__parent"), slug=slug)
    related = (
        Product.objects.active().filter(category=item.category).exclude(pk=item.pk)[:4]
    )
    return render(request, "product.html", {"product": item, "gallery": item.gallery, "related": related})
