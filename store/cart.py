"""Session-backed cart. Prices always come from the database or data.FRAME_BUILDER, never from the browser."""
from decimal import Decimal

from django.conf import settings

from . import data
from .models import Product

SESSION_KEY = "cart"
MAX_QTY = 20


def _pick(group, key):
    return next((x for x in data.FRAME_BUILDER[group] if x["key"] == key), None)


def clean_framing_options(opts):
    """Validate framing choices against the builder config. Returns (options, unit_price) or (None, None)."""
    size, frame = _pick("sizes", opts.get("size")), _pick("frames", opts.get("frame"))
    width, glazing = _pick("widths", opts.get("width")), _pick("glazing", opts.get("glazing"))
    mat = _pick("mats", opts.get("mat"))
    if not (size and frame and width and glazing):
        return None, None
    if width["key"] != "none" and not mat:
        return None, None
    options = {
        "size": size["key"], "frame": frame["key"], "width": width["key"], "glazing": glazing["key"],
        "mat": mat["key"] if width["key"] != "none" and mat else "",
    }
    # Keep in sync with the price formula in static/js/home.js.
    price = Decimal(round(size["base"] * frame["mult"])) + width["add"] + glazing["add"]
    return options, price


def framing_summary(options):
    parts = [
        _pick("sizes", options["size"])["label"],
        _pick("frames", options["frame"])["label"],
        "no mat" if options["width"] == "none" else f'{_pick("widths", options["width"])["label"].lower()} {_pick("mats", options["mat"])["label"].lower()} mat',
        _pick("glazing", options["glazing"])["label"].lower(),
    ]
    return ", ".join(parts)


def shipping_for(subtotal):
    if subtotal <= 0 or subtotal >= data.FREE_SHIPPING_THRESHOLD:
        return Decimal("0")
    return Decimal(getattr(settings, "SHIPPING_FEE", 99))


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

    def add_framing(self, options, qty=1):
        options, price = clean_framing_options(options or {})
        if not options:
            return False
        key = "f-" + "-".join(options[k] or "x" for k in ("size", "frame", "width", "mat", "glazing"))
        line = self.raw.setdefault(key, {"kind": "framing", "options": options, "qty": 0})
        line["qty"] = min(line["qty"] + max(qty, 1), MAX_QTY)
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
            if l["kind"] == "product":
                p = products.get(l["id"])
                if not p or not p.in_stock:
                    stale.append(key)
                    continue
                qty = min(l["qty"], p.stock, MAX_QTY)
                out.append({
                    "key": key, "kind": "product", "product": p, "name": p.name, "by": p.brand,
                    "icon": p.icon, "colors": p.c, "unit_price": p.price, "qty": qty,
                    "max_qty": min(p.stock, MAX_QTY), "options": {},
                })
            else:
                options, price = clean_framing_options(l["options"])
                if not options:
                    stale.append(key)
                    continue
                out.append({
                    "key": key, "kind": "framing", "product": None, "name": "Custom framing",
                    "by": framing_summary(options), "icon": "a-frame",
                    "colors": ["#F1F1EE", data.ULTRAMARINE, data.GOLD], "unit_price": price,
                    "qty": l["qty"], "max_qty": MAX_QTY, "options": options,
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
        threshold = Decimal(data.FREE_SHIPPING_THRESHOLD)
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
                    "price": float(l["unit_price"]), "qty": l["qty"], "max_qty": l["max_qty"],
                    "line_total": float(l["line_total"]),
                }
                for l in s["lines"]
            ],
        }
