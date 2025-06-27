from PIL import Image, ImageDraw, ImageFont
import re
import logging


async def generate_color_swatch(hex_code: str):
    """
    Generates a color swatch image for a given hex color code.

    :param hex_code: The hex color code (with or without leading '#')
    :return: Tuple of (status message, PIL Image or None)
    """
    # Normalize hex code (remove leading # if present)
    if hex_code.startswith('#'):
        hex_code = hex_code[1:]

    # Validate hex code (3 or 6 hex digits)
    if not re.fullmatch(r'[0-9a-fA-F]{6}|[0-9a-fA-F]{3}', hex_code):
        logging.warning(f"Failed to generate color swatch for {hex_code}")
        return f"Failed to generate color swatch for {hex_code}", None
    
    # Expand 3-digit hex to 6-digit
    if len(hex_code) == 3:
        hex_code = ''.join([c*2 for c in hex_code])

    # Convert to RGB tuple
    rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    # Create 200x200 image (larger for clearer text)
    img = Image.new('RGB', (200, 200), rgb)

    # Draw hex code in top left corner
    draw = ImageDraw.Draw(img)
    try:
        # Use a larger font size for clarity
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 36)
        except Exception:
            font = ImageFont.load_default()

    text = f"#{hex_code.upper()}"
    x, y = 8, 8
    outline_color = (255, 255, 255) if sum(rgb) < 384 else (0, 0, 0)
    
    # Draw outline
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                draw.text((x+dx, y+dy), text, font=font, fill=outline_color)
    
    # Draw main text
    text_color = (0, 0, 0) if sum(rgb) > 384 else (255, 255, 255)
    draw.text((x, y), text, font=font, fill=text_color)

    logging.info(f"Generated new color swatch for {hex_code}")
    return f"Generated color swatch for {hex_code}", img
