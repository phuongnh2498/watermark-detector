from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """Create a simple icon for the application"""
    # Create a 1024x1024 image with a white background
    icon_size = 1024
    img = Image.new("RGBA", (icon_size, icon_size), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw a blue circle as the background
    circle_radius = icon_size // 2 - 50
    circle_center = (icon_size // 2, icon_size // 2)
    draw.ellipse(
        (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius,
        ),
        fill=(65, 105, 225, 255),  # Royal Blue
    )

    # Draw a "W" in the center
    try:
        # Try to use a font if available
        font = ImageFont.truetype("Arial.ttf", size=icon_size // 2)
    except IOError:
        # Fall back to default font
        font = ImageFont.load_default()

    text = "W"
    # For newer Pillow versions
    if hasattr(font, "getbbox"):
        bbox = font.getbbox(text)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    else:
        # Fallback for older Pillow versions
        text_width, text_height = (
            draw.textsize(text, font=font)
            if hasattr(draw, "textsize")
            else (icon_size // 3, icon_size // 3)
        )

    text_position = (
        circle_center[0] - text_width // 2,
        circle_center[1] - text_height // 2,
    )
    draw.text(text_position, text, fill=(255, 255, 255, 255), font=font)

    # Save as PNG
    img.save("app_icon.png")

    # For macOS, convert to ICNS
    if os.path.exists("/usr/bin/sips") and os.path.exists("/usr/bin/iconutil"):
        # Create iconset directory
        os.makedirs("app_icon.iconset", exist_ok=True)

        # Generate different sizes
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(f"app_icon.iconset/icon_{size}x{size}.png")
            # Also create 2x versions
            if size * 2 <= 1024:
                resized = img.resize((size * 2, size * 2), Image.LANCZOS)
                resized.save(f"app_icon.iconset/icon_{size}x{size}@2x.png")

        # Convert to icns
        os.system("iconutil -c icns app_icon.iconset")

        # Clean up
        import shutil

        shutil.rmtree("app_icon.iconset")

    # For Windows, save as ICO
    sizes = [16, 32, 48, 64, 128, 256]
    icon_sizes = [(size, size) for size in sizes]

    # Create resized versions
    resized_images = []
    for size in icon_sizes:
        resized = img.resize(size, Image.LANCZOS)
        resized_images.append(resized)

    # Save as ICO
    img.save("app_icon.ico", format="ICO", sizes=icon_sizes)

    print("Icon files created: app_icon.png and platform-specific icons")


if __name__ == "__main__":
    create_icon()
