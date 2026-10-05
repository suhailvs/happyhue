from django import template

register = template.Library()


@register.filter
def inr(value):
    """Format a number as rupees with Indian digit grouping: 123456 -> ₹1,23,456."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    digits = str(abs(n))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"₹{'-' if n < 0 else ''}{digits}"


@register.filter
def css_vars(colors):
    """['#2A3BD0', '#E8B02E'] -> '--c1:#2A3BD0;--c2:#E8B02E;--c3:#2A3BD0'.

    The SVG illustrations in partials/sprite.html read --c1, --c2 and --c3.
    """
    colors = list(colors)
    c1 = colors[0]
    c2 = colors[1] if len(colors) > 1 else c1
    c3 = colors[2] if len(colors) > 2 else c1
    return f"--c1:{c1};--c2:{c2};--c3:{c3}"
