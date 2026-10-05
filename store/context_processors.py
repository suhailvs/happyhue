from . import data


def storefront(request):
    """Values every page needs: header menus, footer columns, cart threshold."""
    return {
        "store_name": data.STORE_NAME,
        "categories": data.CATEGORIES,
        "free_shipping_threshold": data.FREE_SHIPPING_THRESHOLD,
        "help_links": data.HELP_LINKS,
    }
