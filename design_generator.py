import os
from PIL import Image, ImageDraw, ImageFont

def load_dynamic_font(font_candidates: list, size: int):
    """
    Attempts to load custom system TTF fonts sequentially.
    Falls back to Pillow's built-in default font if no specified TTF file exists on the host system.
    """
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()

def generate_streetwear_design(
    top_text: str = "WEST COAST",
    hero_text: str = "LOS ANGELES",
    script_text: str = "California",
    bottom_text: str = "SINCE 1985",
    output_path: str = "generated_design.png",
    text_color: tuple = (20, 20, 20, 255)  # Dark charcoal ink for light/white apparel
) -> str:
    """
    Generates a high-resolution (4500x5400 px, 300 DPI) transparent PNG 
    recreating the 4-tier vintage varsity / athletic streetwear layout.
    """
    # 1. Canvas Setup: Standard Print-on-Demand printable area dimensions
    WIDTH, HEIGHT = 4500, 5400
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 2. Load specialized typography fonts for each tier of the layout
    font_top = load_dynamic_font(["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"], 130)
    font_hero = load_dynamic_font(["impact.ttf", "Impact.ttf", "arialbd.ttf"], 480)
    font_script = load_dynamic_font(["georgiai.ttf", "timesi.ttf", "DejaVuSerif-Italic.ttf"], 190)
    font_bottom = load_dynamic_font(["arialbd.ttf", "Arial Bold.ttf"], 110)

    # 3. Define vertical starting point (positioned near the chest placement region)
    current_y = 1600

    # ---------------------------------------------------------------------------
    # TIER 1: Top Sub-header (Wide letter-spacing / tracking)
    # ---------------------------------------------------------------------------
    top_spaced = "  ".join(list(top_text.upper().strip()))
    bbox1 = font_top.getbbox(top_spaced)
    w1 = bbox1[2] - bbox1[0]
    draw.text(((WIDTH - w1) // 2, current_y), top_spaced, font=font_top, fill=text_color)
    current_y += 240

    # ---------------------------------------------------------------------------
    # TIER 2: Main Hero Title (Massive bold block lettering)
    # ---------------------------------------------------------------------------
    hero_clean = hero_text.upper().strip()
    bbox2 = font_hero.getbbox(hero_clean)
    w2 = bbox2[2] - bbox2[0]
    draw.text(((WIDTH - w2) // 2, current_y), hero_clean, font=font_hero, fill=text_color)
    current_y += 520

    # ---------------------------------------------------------------------------
    # TIER 3: Middle Script Accent with Flanking Decorative Bars
    # ---------------------------------------------------------------------------
    script_clean = f" {script_text.strip()} "
    bbox3 = font_script.getbbox(script_clean)
    w3 = bbox3[2] - bbox3[0]
    script_x = (WIDTH - w3) // 2
    
    # Draw script text
    draw.text((script_x, current_y), script_clean, font=font_script, fill=text_color)

    # Draw left and right horizontal accent lines aligned to text height
    line_y = current_y + 95
    line_length = 350
    line_thickness = 12
    
    # Left decorative bar
    draw.line([(script_x - line_length - 40, line_y), (script_x - 40, line_y)], fill=text_color, width=line_thickness)
    # Right decorative bar
    draw.line([(script_x + w3 + 40, line_y), (script_x + w3 + line_length + 40, line_y)], fill=text_color, width=line_thickness)
    
    current_y += 280

    # ---------------------------------------------------------------------------
    # TIER 4: Bottom Sub-header (Spaced vintage tag line)
    # ---------------------------------------------------------------------------
    bottom_spaced = "  ".join(list(bottom_text.upper().strip()))
    bbox4 = font_bottom.getbbox(bottom_spaced)
    w4 = bbox4[2] - bbox4[0]
    draw.text(((WIDTH - w4) // 2, current_y), bottom_spaced, font=font_bottom, fill=text_color)

    # 4. Save transparent PNG with embedded 300 DPI metadata for print readiness
    canvas.save(output_path, "PNG", dpi=(300, 300))
    print(f"✨ Design successfully generated and saved to: '{os.path.abspath(output_path)}'")
    
    return os.path.abspath(output_path)

if __name__ == "__main__":
    # Test execution: Generates the exact layout seen in your sample mockup
    generate_streetwear_design(
        top_text="WEST COAST",
        hero_text="LOS ANGELES",
        script_text="California",
        bottom_text="SINCE 1985",
        output_path="test_varsity_design.png"
    )
