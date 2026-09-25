import os
import math
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# COLOR PALETTES (High-contrast streetwear & retrowave themes)
# ---------------------------------------------------------------------------
COLOR_PALETTES = [
    {
        "name": "Cyberpunk Neon",
        "primary": (0, 255, 204, 255),    # Cyan
        "secondary": (255, 0, 128, 255),  # Magenta
        "accent": (255, 230, 0, 255),     # Yellow
        "text": (255, 255, 255, 255)      # White
    },
    {
        "name": "Retro Sunset",
        "primary": (255, 94, 0, 255),     # Electric Orange
        "secondary": (255, 0, 90, 255),   # Hot Pink
        "accent": (255, 200, 0, 255),    # Gold
        "text": (240, 240, 240, 255)     # Off-White
    },
    {
        "name": "Acid Graphic",
        "primary": (170, 255, 0, 255),    # Acid Lime
        "secondary": (0, 180, 255, 255),  # Bright Blue
        "accent": (255, 255, 255, 255),   # White
        "text": (170, 255, 0, 255)       # Acid Lime
    },
    {
        "name": "Monochrome Tech",
        "primary": (255, 255, 255, 255),  # White
        "secondary": (180, 180, 180, 255),# Light Grey
        "accent": (255, 60, 60, 255),    # Red Accent
        "text": (255, 255, 255, 255)      # White
    }
]

def load_dynamic_font(font_size: int):
    """
    Attempts to load custom system fonts (Impact, Arial Black, Trebuchet MS).
    Falls back to Pillow's built-in default font if custom TTF files are missing.
    """
    font_candidates = [
        "impact.ttf", "Impact.ttf", 
        "arialbd.ttf", "Arial Bold.ttf", 
        "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, font_size)
        except OSError:
            continue
    # Fallback if no TTF font is found on the host system
    return ImageFont.load_default()

def draw_retro_sun(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, radius: int, palette: dict):
    """
    Draws a 1980s synthwave-style sun with horizontal sliced stripes.
    """
    primary_color = palette["primary"]
    secondary_color = palette["secondary"]

    # Top boundary and bottom boundary of the sun bounding box
    bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
    
    # Draw top solid half using primary color
    draw.chord(bbox, start=180, end=360, fill=primary_color)

    # Draw bottom half with expanding horizontal cutouts
    num_stripes = 7
    stripe_height = radius // (num_stripes * 2)
    
    for i in range(num_stripes):
        y_top = center_y + (i * stripe_height * 2)
        y_bottom = y_top + stripe_height + (i * 2)  # Stripes widen towards the bottom
        
        if y_bottom > center_y + radius:
            break

        # Calculate bounding arc angle slice for current stripe
        dy = y_top - center_y
        if abs(dy) < radius:
            angle = math.degrees(math.acos(dy / radius))
            start_angle = 90 - angle
            end_angle = 90 + angle
            draw.arc(bbox, start=start_angle, end=end_angle, fill=secondary_color, width=stripe_height)

def draw_tech_crosshairs(draw: ImageDraw.ImageDraw, width: int, height: int, palette: dict):
    """
    Draws subtle Y2K streetwear technical markers, crosshairs, and framing lines.
    """
    accent_color = palette["accent"]
    
    # Center crosshair coordinates
    cx, cy = width // 2, height // 2 - 200
    size = 120
    line_width = 8

    # Draw center target crosshair
    draw.line([(cx - size, cy), (cx + size, cy)], fill=accent_color, width=line_width)
    draw.line([(cx, cy - size), (cx, cy + size)], fill=accent_color, width=line_width)
    draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], outline=accent_color, width=line_width)

    # Outer corner framing brackets
    margin_x, margin_y = 600, 800
    bracket_len = 150
    
    # Top-Left Bracket
    draw.line([(margin_x, margin_y), (margin_x + bracket_len, margin_y)], fill=accent_color, width=line_width)
    draw.line([(margin_x, margin_y), (margin_x, margin_y + bracket_len)], fill=accent_color, width=line_width)
    
    # Top-Right Bracket
    draw.line([(width - margin_x, margin_y), (width - margin_x - bracket_len, margin_y)], fill=accent_color, width=line_width)
    draw.line([(width - margin_x, margin_y), (width - margin_x, margin_y + bracket_len)], fill=accent_color, width=line_width)

def render_layered_text(draw: ImageDraw.ImageDraw, text: str, width: int, start_y: int, palette: dict):
    """
    Renders multi-line streetwear typography with a 3D offset shadow effect.
    """
    # Clean text and split long titles into two balanced lines
    words = text.upper().split()
    if len(words) > 2:
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [text.upper()]

    font_size = 280
    font = load_dynamic_font(font_size)
    text_color = palette["text"]
    shadow_color = palette["secondary"]

    current_y = start_y

    for line in lines:
        # Measure text width to center align horizontally
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2

        # 1. Draw 3D Drop-Shadow (offset diagonally by 18px)
        shadow_offset = 18
        draw.text((x + shadow_offset, current_y + shadow_offset), line, font=font, fill=shadow_color)

        # 2. Draw Foreground Primary Text
        draw.text((x, current_y), line, font=font, fill=text_color)

        # Increment vertical position for next line
        current_y += text_height + 80

def generate_streetwear_design(title_text: str = "RETRO GLITCH", output_path: str = "generated_design.png") -> str:
    """
    Main function: Generates a high-resolution (4500x5400 px, 300 DPI) transparent PNG 
    graphic tee artwork completely programmatically using Python Pillow.
    """
    # 1. Canvas setup: Standard Printify DTG printable canvas dimensions
    WIDTH, HEIGHT = 4500, 5400
    
    # Create blank RGBA image with 100% transparent background
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 2. Pick a random color palette to ensure artwork variety on every execution
    palette = random.choice(COLOR_PALETTES)
    print(f"🎨 Generating design using palette: '{palette['name']}'...")

    # 3. Draw background vector graphics (Retro Sun & Tech Markings)
    sun_center_x = WIDTH // 2
    sun_center_y = (HEIGHT // 2) - 300
    sun_radius = 900
    
    draw_retro_sun(draw, sun_center_x, sun_center_y, sun_radius, palette)
    draw_tech_crosshairs(draw, WIDTH, HEIGHT, palette)

    # 4. Render main typography title
    render_layered_text(draw, title_text, WIDTH, start_y=3100, palette=palette)

    # 5. Save final high-res transparent PNG image file
    canvas.save(output_path, "PNG", dpi=(300, 300))
    print(f"✨ Design successfully generated and saved to: '{os.path.abspath(output_path)}'")
    
    return os.path.abspath(output_path)

if __name__ == "__main__":
    # Test script locally when executed directly
    generate_streetwear_design("CYBERPUNK GLITCH TEE", "test_streetwear_design.png")
