"""Session-backed cart. Prices always come from the database or data.FRAME_BUILDER, never from the browser."""
from decimal import Decimal

from .models import GeneralSettings, Product

SESSION_KEY = "cart"
MAX_QTY = 20



def shipping_for(subtotal):
    threshold = Decimal(GeneralSettings.get_value("free_shipping_threshold", "1999"))
    if subtotal <= 0 or subtotal >= threshold:
        return Decimal("0")
    return Decimal(GeneralSettings.get_value("shipping_fee", "1"))


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.raw = self.session.setdefault(SESSION_KEY, {})

    def _save(self):
        self.session.modified = True

    # --- mutations -------------------------------------------------
    def add_product(self, product_id, qty=1):
        product = Product.objects.active().filter(pk=product_id).first()
        if not product or not product.in_stock:
            return False
        key = f"p{product.pk}"
        line = self.raw.setdefault(key, {"kind": "product", "id": product.pk, "qty": 0})
        line["qty"] = min(line["qty"] + max(qty, 1), product.stock, MAX_QTY)
        self._save()
        return True

    def set_qty(self, key, qty):
        if key not in self.raw:
            return
        if qty <= 0:
            del self.raw[key]
        else:
            self.raw[key]["qty"] = min(qty, MAX_QTY)
        self._save()

    def remove(self, key):
        self.raw.pop(key, None)
        self._save()

    def clear(self):
        self.session[SESSION_KEY] = {}
        self._save()

    # --- reading ---------------------------------------------------
    def lines(self):
        product_ids = [l["id"] for l in self.raw.values() if l["kind"] == "product"]
        products = Product.objects.active().in_bulk(product_ids)
        out, stale = [], []
        for key, l in self.raw.items():
            p = products.get(l["id"]) if l.get("kind") == "product" else None
            if not p or not p.in_stock:
                stale.append(key)
                continue
            qty = min(l["qty"], p.stock, MAX_QTY)
            out.append({
                "key": key, "kind": "product", "product": p, "name": p.name, "by": p.brand,
                "icon": p.icon, "colors": p.c, "unit_price": p.price, "qty": qty,
                "image": p.main_image.image.url if p.main_image else "", "url": p.get_absolute_url(),
                "max_qty": min(p.stock, MAX_QTY), "options": {},
            })
        for key in stale:
            del self.raw[key]
        if stale:
            self._save()
        for line in out:
            line["line_total"] = line["unit_price"] * line["qty"]
        return out

    def summary(self):
        lines = self.lines()
        subtotal = sum((l["line_total"] for l in lines), Decimal("0"))
        shipping = shipping_for(subtotal)
        return {
            "lines": lines,
            "count": sum(l["qty"] for l in lines),
            "subtotal": subtotal,
            "shipping": shipping,
            "total": subtotal + shipping,
        }

    def as_json(self):
        s = self.summary()
        threshold = Decimal(GeneralSettings.get_value("free_shipping_threshold", "1999"))
        return {
            "count": s["count"],
            "subtotal": float(s["subtotal"]),
            "shipping": float(s["shipping"]),
            "total": float(s["total"]),
            "threshold": float(threshold),
            "remaining": float(max(threshold - s["subtotal"], 0)),
            "lines": [
                {
                    "key": l["key"], "name": l["name"], "by": l["by"], "icon": l["icon"], "colors": l["colors"],
                    "image": l["image"], "url": l["url"],
                    "price": float(l["unit_price"]), "qty": l["qty"], "max_qty": l["max_qty"],
                    "line_total": float(l["line_total"]),
                }
                for l in s["lines"]
            ],
        }
