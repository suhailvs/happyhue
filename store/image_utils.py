import os
from io import BytesIO
 
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
 
 
def optimize_image(field_file, max_size=(1600, 1600), quality=80):
    """Resize to fit max_size, fix phone rotation, convert to WebP.
    Returns (new_name, ContentFile)."""
    img = Image.open(field_file)
    img = ImageOps.exif_transpose(img)  # phone photos often have rotation metadata
 
    # WebP handles RGB and RGBA; convert anything else (CMYK, palette, etc.)
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    img = img.convert("RGBA" if has_alpha else "RGB")
 
    img.thumbnail(max_size, Image.LANCZOS)  # only shrinks, never enlarges
 
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
 
    base = os.path.splitext(os.path.basename(field_file.name))[0]
    return f"{base}.webp", ContentFile(buf.getvalue())
