"""Static catalog data for the storefront.

Categories and products live in the database (store/models.py). Run
`python manage.py seed_catalog` to load the CATEGORIES and PRODUCTS below.
After that, CATEGORIES is only read for presentation (hero panel colors,
promos, headline verbs) and PRODUCTS only by the seed command.

Colors are pigment hex values. A `c` list is [c1, c2, c3] and feeds the SVG
illustrations through the `css_vars` template filter.
"""

STORE_NAME = "Happyhue"
FREE_SHIPPING_THRESHOLD = 1999

ULTRAMARINE = "#2A3BD0"
GOLD = "#E8B02E"
VIRIDIAN = "#0F7B63"
ROSE = "#C8445F"
INK = "#131A33"

CATEGORIES = [
    {
        "slug": "art-materials",
        "anchor": "materials",
        "name": "Art materials",
        "verb": "Paint it.",
        "tagline": "Everything for the first wash and the final layer.",
        "panel_text": "Paints, brushes, papers and drawing tools from brands we trust.",
        "cta": "Shop art materials",
        "see_all": "Shop all art materials",
        "panel": {"bg": ULTRAMARINE, "ink": "#FFFFFF"},
        "panel_art": [
            {"icon": "a-tube", "x": 6, "y": 130, "size": 190, "c": ["#FFD24C", "#FFFFFF"]},
            {"icon": "a-tube", "x": 120, "y": 14, "size": 190, "c": ["#F2708A", "#FFFFFF"]},
            {"icon": "a-brush", "x": 132, "y": 146, "size": 200, "c": ["#FFFFFF", "#FFD24C"]},
        ],
        "promo": {
            "title": "Watercolor sets for first washes",
            "link": "Shop new arrivals",
            "href": "#shop",
            "bg": ULTRAMARINE,
            "icon": "a-tube",
            "c": ["#FFD24C", "#FFFFFF"],
        },
        "children": [
            {"slug": "colors", "name": "Colors", "blurb": "Watercolor, acrylic, oil and gouache",
             "count_label": "312 items", "icon": "a-tube", "c": [ULTRAMARINE, "#9AA3B8", GOLD]},
            {"slug": "brushes", "name": "Brushes", "blurb": "Rounds, flats and complete sets",
             "count_label": "186 items", "icon": "a-brush", "c": ["#7A4B2A", ROSE, GOLD]},
            {"slug": "surfaces", "name": "Surfaces", "blurb": "Paper pads, canvas and boards",
             "count_label": "148 items", "icon": "a-pad", "c": [VIRIDIAN, "#9AA3B8", "#4C7BE0"]},
            {"slug": "drawing", "name": "Drawing", "blurb": "Pencils, charcoal and pens",
             "count_label": "154 items", "icon": "a-pencil", "c": [GOLD, VIRIDIAN, ROSE]},
        ],
    },
    {
        "slug": "handmade",
        "anchor": "handmade",
        "name": "Handmade",
        "verb": "Make it.",
        "tagline": "Original pieces from local makers, each one a little different.",
        "panel_text": "Original paintings and small-batch pieces by local artists and craftspeople.",
        "cta": "Shop handmade",
        "see_all": "Shop all handmade",
        "panel": {"bg": GOLD, "ink": INK},
        "panel_art": [
            {"icon": "a-dream", "x": 70, "y": 0, "size": 250, "c": [INK, ROSE, ULTRAMARINE]},
            {"icon": "a-pouch", "x": 0, "y": 196, "size": 150, "c": [VIRIDIAN, INK, "#F6E7B4"]},
            {"icon": "a-book", "x": 176, "y": 196, "size": 150, "c": [ULTRAMARINE, "#FFFFFF"]},
        ],
        "promo": None,
        "children": [
            {"slug": "paintings-original", "name": "Paintings original",
             "blurb": "One-of-one works from local artists, framed and ready to hang.",
             "menu_blurb": "One-of-one works from local artists",
             "count_label": "24 originals", "icon": "a-painting", "c": [VIRIDIAN, "#8B5A3C", GOLD]},
            {"slug": "sketchbooks-journals", "name": "Sketchbooks and journals",
             "blurb": "Hand-stitched in kraft and cloth", "menu_blurb": "Hand-stitched in kraft and cloth",
             "count_label": "41 items", "icon": "a-book", "c": ["#8B5A3C", GOLD]},
            {"slug": "dream-catchers", "name": "Dream catchers",
             "blurb": "Woven by hand with feathers and beads", "menu_blurb": "Woven by hand with feathers and beads",
             "count_label": "18 items", "icon": "a-dream", "c": [ROSE, GOLD, VIRIDIAN]},
            {"slug": "pouches", "name": "Pouches",
             "blurb": "Block-printed and zipped", "menu_blurb": "Block-printed and zipped",
             "count_label": "33 items", "icon": "a-pouch", "c": [ULTRAMARINE, GOLD, "#F6E7B4"]},
            {"slug": "scrapbooks", "name": "Scrapbooks",
             "blurb": "Albums and kits for keepsakes", "menu_blurb": "Albums and kits for keepsakes",
             "count_label": "15 items", "icon": "a-scrap", "c": [GOLD, ROSE, ULTRAMARINE]},
        ],
    },
    {
        "slug": "art-framing",
        "anchor": "framing",
        "name": "Art framing",
        "verb": "Frame it.",
        "tagline": "Pick a size, a frame and a mat. The preview updates as you choose.",
        "panel_text": "Frames cut to your artwork, with acid-free mats and your choice of glazing.",
        "cta": "Design your frame",
        "see_all": "",
        "panel": {"bg": VIRIDIAN, "ink": "#FFFFFF"},
        "panel_art": [
            {"icon": "a-frame", "x": 50, "y": 20, "size": 290, "c": ["#F1F1EE", ULTRAMARINE, GOLD]},
            {"icon": "a-frame", "x": 0, "y": 206, "size": 130, "c": [INK, GOLD, ROSE]},
        ],
        "promo": {
            "title": "Design your frame and see it live",
            "link": "Open the frame builder",
            "href": "#framing",
            "bg": VIRIDIAN,
            "icon": "a-frame",
            "c": ["#F1F1EE", ULTRAMARINE, GOLD],
        },
        "children": [
            {"slug": "custom-framing", "name": "Custom framing",
             "blurb": "Cut to your artwork, ready in 5 to 7 days",
             "menu_blurb": "Cut to your artwork, ready in 5 to 7 days",
             "count_label": "", "icon": "a-frame", "c": ["#F1F1EE", ULTRAMARINE, GOLD]},
        ],
    },
]

_PRODUCT_LIST = [
    {"id": "p1",  "category": "colors","name": "Essentials watercolor set, 6 tubes of 5 ml", "by": "Daniel Smith", "price": 4199,
     "icon": "a-tube", "c": [ULTRAMARINE, "#8E97AE"], "badge": "Bestseller"},
    {"id": "p2", "category": "brushes",  "name": "Anna Mason brush set of 5", "by": "RoseMary", "price": 3345,
     "icon": "a-brush", "c": ["#1F2A5C", "#B77B4A"]},
    {"id": "p3", "category": "colors", "name": "Quinacridone Gold watercolor, 5 ml tube", "by": "Daniel Smith", "price": 899,
     "icon": "a-tube", "c": [GOLD, "#8E97AE"], "badge": "Bestseller"},
    {"id": "p4",  "category": "surfaces","name": "Cold press watercolor pad, A4, 300 gsm", "by": "Hahnemühle", "price": 1150,
     "icon": "a-pad", "c": [VIRIDIAN, "#E3E7F1", "#4C7BE0"]},
    {"id": "p5",  "category": "drawing", "name": "Graphite drawing pencils, set of 12", "by": "Camel", "price": 640, "old_price": 790,
     "icon": "a-pencil", "c": [GOLD, VIRIDIAN, ROSE], "badge": "Sale"},
    {"id": "p6", "category": "dream-catchers", "name": "Hand-painted dream catcher, 20 cm", "by": "Handmade by Meera", "price": 750,
     "icon": "a-dream", "c": [ROSE, GOLD, VIRIDIAN], "badge": "New"},
    {"id": "p7", "category": "pouches","name": "Block-printed zip pouch, pencil size", "by": "Handmade by Fathima", "price": 420,
     "icon": "a-pouch", "c": [VIRIDIAN, GOLD, "#F6E7B4"]},
    {"id": "p8", "category": "sketchbooks-journals",  "name": "Hand-stitched sketchbook, 120 pages", "by": "Handmade by Anwar", "price": 980,
     "icon": "a-book", "c": ["#8B5A3C", GOLD]},
    {"id": "p9", "category": "paintings-original", "stock": 1,"name": "Original acrylic landscape, 12 × 16 in", "by": "Handmade by Meera", "price": 6500,
     "icon": "a-painting", "c": [VIRIDIAN, "#8B5A3C", GOLD], "badge": "One of one"},
    {"id": "p10","category": "scrapbooks",  "name": "Scrapbook album with kraft pages", "by": "Handmade by Anwar", "price": 860,
     "icon": "a-scrap", "c": [ROSE, GOLD, ULTRAMARINE]},
    {"id": "p11", "category": "colors","name": "Cobalt Teal Blue watercolor, 5 ml tube", "by": "Daniel Smith", "price": 899,
     "icon": "a-tube", "c": ["#1AA6A0", "#8E97AE"], "badge": "New"},
    {"id": "p12", "category": "brushes", "name": "Synthetic round brush, size 6", "by": "Silver Brush", "price": 560,
     "icon": "a-brush", "c": [VIRIDIAN, "#7A4B2A"], "badge": "New"},
]
PRODUCTS = {p["id"]: p for p in _PRODUCT_LIST}

# (key, label, product ids in display order)
PRODUCT_TABS = [
    ("best", "Bestsellers", ["p1", "p2", "p3", "p4"]),
    ("new", "New arrivals", ["p5", "p6", "p11", "p12"]),
    ("hand", "Handmade picks", ["p7", "p8", "p9", "p10"]),
]


WHY_US = [
    {"title": "Tested by artists", "text": "If it is on the shelf, someone on our team has painted with it.", "color": ULTRAMARINE},
    {"title": "Packed for the post", "text": "Glass tubes, palettes and frames are wrapped the way artists wish every store did.", "color": GOLD},
    {"title": "Made by local hands", "text": "Handmade pieces come straight from the people who made them, with their names on the listing.", "color": ROSE},
    {"title": "Real answers", "text": "Ask about a paper’s sizing or a pigment’s lightfastness and a person replies.", "color": VIRIDIAN},
]


# HELP_LINKS = ["Track order", "Shipping and returns", "Learning center", "Contact"]

# Frame builder: rendered as radio inputs in home.html and sent to
# static/js/home.js with json_script so prices and preview use the same numbers.
QUOTE_SIZES = [
    {"key": "small", "label": "Small (up to A4)"},
    {"key": "medium", "label": "Medium (up to A3)"},
    {"key": "large", "label": "Large (A2 and above)"},
    {"key": "custom", "label": "Custom / not sure"},
]