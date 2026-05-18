# From: claude_backend/tray.py:38
# Render a 64x64 tray icon. Green dot = installed, gray = not.

def _make_icon_image(installed: bool = True) -> Image.Image:
    """Render a 64x64 tray icon. Green dot = installed, gray = not."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background coin: dark navy circle
    draw.ellipse((4, 4, ICON_SIZE - 4, ICON_SIZE - 4), fill=(30, 60, 110, 255))

    # "T" letter centered
    try:
        font = ImageFont.truetype("seguibl.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    text = "T"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        ((ICON_SIZE - tw) // 2, (ICON_SIZE - th) // 2 - 4),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )

    # Status dot bottom-right: green if installed, gray if not
    dot_color = (16, 124, 16, 255) if installed else (120, 120, 120, 255)
    draw.ellipse((44, 44, 60, 60), fill=dot_color, outline=(255, 255, 255, 255), width=2)

    return img
