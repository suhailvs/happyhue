from . import data

from .navigation import get_navigation
from .models import GeneralSettings
from django.conf import settings


def asset_version(request):
    return {"ASSET_VERSION": settings.ASSET_VERSION}

def storefront(request):
    """Values every page needs: header menus, footer columns, cart threshold."""
    return {
        "store_name": data.STORE_NAME,
        "categories": get_navigation(request),
        "free_shipping_threshold": GeneralSettings.get_value("free_shipping_threshold", "1999"),
        # "help_links": data.HELP_LINKS,
    }
