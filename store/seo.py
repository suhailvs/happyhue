from xml.sax.saxutils import escape

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse

from .models import Category, Product


def robots_txt(request):
    body = "\n".join(
        [
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /cart/",
            "Disallow: /checkout/",
            "Disallow: /addresses/",
            "Disallow: /accounts/",
            "Disallow: /webhooks/",
            f"Sitemap: {settings.SITE_URL}{reverse('sitemap')}",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    """Publish indexable storefront URLs on the configured canonical host."""
    urls = [reverse("store:home")]
    urls.extend(
        reverse("store:category", args=[slug])
        for slug in Category.objects.filter(is_active=True).values_list("slug", flat=True)
    )
    urls.extend(
        reverse("store:product", args=[slug])
        for slug in Product.objects.active().values_list("slug", flat=True)
    )
    entries = "".join(f"<url><loc>{escape(settings.SITE_URL + path)}</loc></url>" for path in urls)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
