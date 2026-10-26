"""Static category presentation data and homepage quote choices.

Categories are loaded into the database by `python manage.py seed_catalog`.
This module keeps the presentation details used by navigation and the home page.

Colors are pigment hex values. A `c` list is [c1, c2, c3] and feeds the SVG
illustrations through the `css_vars` template filter.
"""

STORE_NAME = "Happyhue"

ULTRAMARINE = "#2A3BD0"
GOLD = "#E8B02E"
VIRIDIAN = "#0F7B63"
ROSE = "#C8445F"

CATEGORIES = [
    {
        "slug": "art-materials",
        "anchor": "materials",
        "name": "Art materials",
        "tagline": "Everything for the first wash and the final layer.",
        "see_all": "Shop all art materials",
        "children": [
            {"slug": "colors", "name": "Colors", "blurb": "Watercolor, acrylic, oil and gouache", "icon": "a-tube", "c": [ULTRAMARINE, "#9AA3B8", GOLD]},
            {"slug": "brushes", "name": "Brushes", "blurb": "Rounds, flats and complete sets", "icon": "a-brush", "c": ["#7A4B2A", ROSE, GOLD]},
            {"slug": "surfaces", "name": "Surfaces", "blurb": "Paper pads, canvas and boards", "icon": "a-pad", "c": [VIRIDIAN, "#9AA3B8", "#4C7BE0"]},
            {"slug": "drawing", "name": "Drawing", "blurb": "Pencils, charcoal and pens", "icon": "a-pencil", "c": [GOLD, VIRIDIAN, ROSE]},
        ],
    },
    {
        "slug": "handmade",
        "anchor": "handmade",
        "name": "Handmade",
        "tagline": "Original pieces from local makers, each one a little different.",
        "see_all": "Shop all handmade",
        "children": [
            {"slug": "paintings-original", "name": "Paintings original",
             "blurb": "One-of-one works from local artists, framed and ready to hang.",
             "menu_blurb": "One-of-one works from local artists", "icon": "a-painting", "c": [VIRIDIAN, "#8B5A3C", GOLD]},
            {"slug": "sketchbooks-journals", "name": "Sketchbooks and journals",
             "blurb": "Hand-stitched in kraft and cloth", "menu_blurb": "Hand-stitched in kraft and cloth", "icon": "a-book", "c": ["#8B5A3C", GOLD]},
            {"slug": "dream-catchers", "name": "Dream catchers",
             "blurb": "Woven by hand with feathers and beads", "menu_blurb": "Woven by hand with feathers and beads", "icon": "a-dream", "c": [ROSE, GOLD, VIRIDIAN]},
            {"slug": "pouches", "name": "Pouches",
             "blurb": "Block-printed and zipped", "menu_blurb": "Block-printed and zipped", "icon": "a-pouch", "c": [ULTRAMARINE, GOLD, "#F6E7B4"]},
            {"slug": "scrapbooks", "name": "Scrapbooks",
             "blurb": "Albums and kits for keepsakes", "menu_blurb": "Albums and kits for keepsakes", "icon": "a-scrap", "c": [GOLD, ROSE, ULTRAMARINE]},
        ],
    },
    {
        "slug": "art-framing",
        "anchor": "framing",
        "name": "Art framing",
        "tagline": "Pick a size, a frame and a mat. The preview updates as you choose.",
        "see_all": "",
        "children": [
            {"slug": "custom-framing", "name": "Custom framing",
             "blurb": "Cut to your artwork, ready in 5 to 7 days",
             "menu_blurb": "Cut to your artwork, ready in 5 to 7 days", "icon": "a-frame", "c": ["#F1F1EE", ULTRAMARINE, GOLD]},
        ],
    },
]

# Artwork sizes offered by the homepage quote form.
QUOTE_SIZES = [
    {"key": "small", "label": "Small (up to A4)"},
    {"key": "medium", "label": "Medium (up to A3)"},
    {"key": "large", "label": "Large (A2 and above)"},
    {"key": "custom", "label": "Custom / not sure"},
]
