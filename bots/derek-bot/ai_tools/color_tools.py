from PIL import Image
import re
import logging


async def generate_color_swatch(hex_code: str):
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

    # Create 50x50 image
    img = Image.new('RGB', (50, 50), rgb)
    logging.info(f"Generated new color swatch for {hex_code}")
    return f"Generated color swatch for {hex_code}", img
