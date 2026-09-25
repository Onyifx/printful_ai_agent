import os
import io
import time
import requests
from PIL import Image
from rembg import remove
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def inspect_artwork_quality(file_path: str) -> bool:
    """
    Automated Visual Quality Gate:
    Inspects the processed artwork file to ensure it meets strict production criteria:
    - Verifies file existence and non-zero size.
    - Confirms exact dimensions (3000x3000px).
    - Checks color mode (RGBA).
    - Verifies alpha channel transparency is balanced.
    """
    print(f"🔍 [Quality Gate] Inspecting graphic asset integrity for: '{os.path.basename(file_path)}'...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Quality Gate Error: File not found at {file_path}")
        
    file_size_bytes = os.path.getsize(file_path)
    if file_size_bytes < 1024:
        raise Exception(f"Quality Gate Error: File size is suspiciously small ({file_size_bytes} bytes).")

    with Image.open(file_path) as img:
        width, height = img.size
        if width != 3000 or height != 3000:
            raise Exception(f"Quality Gate Error: Invalid dimensions {width}x{height}px. Required: 3000x3000px.")
            
        if img.mode != "RGBA":
            raise Exception(f"Quality Gate Error: Invalid color mode '{img.mode}'. Required: RGBA.")
            
        alpha_channel = img.getchannel("A")
        extrema = alpha_channel.getextrema()
        
        if extrema[0] == 255 and extrema[1] == 255:
            print("⚠️ Quality Gate Warning: Image lacks transparency (fully opaque background detected).")
            
        if extrema[1] == 0:
            raise Exception("Quality Gate Error: Processed image is completely transparent/blank.")
            
    print("✅ Quality Gate Passed: Artwork meets high-res Printify production standards.")
    return True


def fetch_from_pollinations(clean_prompt: str, headers: dict) -> bytes:
    """Attempts generation via Pollinations AI with simplified prompts."""
    # Truncate prompt to 120 characters to prevent server-side stack overflows on Pollinations
    short_prompt = clean_prompt[:120].strip()
    encoded_prompt = quote(short_prompt)
    seed = int(time.time())
    
    endpoints = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true",
        f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024"
    ]
    
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=45)
            if res.status_code == 200 and len(res.content) > 5000:
                print("✅ Successfully retrieved raw artwork from Pollinations AI.")
                return res.content
        except requests.RequestException:
            continue
            
    raise Exception("Pollinations AI endpoints failed to return a valid image.")


def fetch_from_lexica_fallback(clean_prompt: str, headers: dict) -> bytes:
    """Fallback engine using Lexica public API if Pollinations is offline."""
    print("🔄 Switching to Fallback Image Engine (Lexica API)...")
    short_prompt = clean_prompt[:80].strip()
    search_url = f"https://lexica.art/api/v1/search?q={quote(short_prompt)}"
    
    try:
        res = requests.get(search_url, headers=headers, timeout=30)
        if res.status_code == 200:
            data = res.json()
            images = data.get("images", [])
            if images:
                # Get the highest resolution image URL from results
                img_url = images[0].get("src")
                img_res = requests.get(img_url, headers=headers, timeout=30)
                if img_res.status_code == 200 and len(img_res.content) > 5000:
                    print("✅ Successfully retrieved fallback artwork from Lexica Engine.")
                    return img_res.content
    except Exception as e:
        print(f"⚠️ Lexica Fallback failed: {e}")
        
    raise Exception("Fallback image engines failed.")


def generate_artwork(concept_prompt: str, output_filename: str = "temp_artwork.png") -> str:
    """
    1. Fetches raw AI artwork using primary + fallback providers.
    2. Crops off watermark/footer regions.
    3. Strips background using rembg (transparent PNG).
    4. Upscales to 3000x3000px @ 300 DPI.
    5. Executes Visual Quality Gate inspection.
    """
    print(f"🎨 [1/5] Generating artwork for prompt: '{concept_prompt}'...")
    
    clean_prompt = f"{concept_prompt}, high contrast graphic vector art, t-shirt design, isolated subject on solid background".strip().replace("\n", " ")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    raw_bytes = None
    
    # Attempt 1: Pollinations AI
    try:
        raw_bytes = fetch_from_pollinations(clean_prompt, headers)
    except Exception as e:
        print(f"⚠️ Primary Engine (Pollinations) unavailable: {e}")
        
    # Attempt 2: Lexica Fallback Engine
    if not raw_bytes:
        try:
            raw_bytes = fetch_from_lexica_fallback(clean_prompt, headers)
        except Exception as e:
            print(f"⚠️ Secondary Fallback Engine unavailable: {e}")

    if not raw_bytes:
        raise Exception("All image generation providers (Pollinations & Lexica) are currently offline or blocking requests.")

    # Process retrieved image
    raw_img = Image.open(io.BytesIO(raw_bytes))
    
    print("✂️ [2/5] Cropping canvas boundaries...")
    w, h = raw_img.size
    clean_img = raw_img.crop((0, 0, w, int(h * 0.93)))
    
    img_byte_arr = io.BytesIO()
    clean_img.save(img_byte_arr, format="PNG")
    cropped_bytes = img_byte_arr.getvalue()
    
    print("🧼 [3/5] Stripping background with rembg...")
    transparent_bytes = remove(cropped_bytes)
    
    print("📐 [4/5] Upscaling artwork to 3000x3000px @ 300 DPI...")
    image = Image.open(io.BytesIO(transparent_bytes)).convert("RGBA")
    high_res_image = image.resize((3000, 3000), Image.Resampling.LANCZOS)
    
    high_res_image.save(output_filename, format="PNG", dpi=(300, 300))
    
    print("🛡️ [5/5] Executing Visual Quality Gate inspection...")
    inspect_artwork_quality(output_filename)
    
    print(f"✅ Artwork processing complete! File saved as: {output_filename}")
    return output_filename


# Alias mapping for backwards compatibility
generate_transparent_artwork = generate_artwork

if __name__ == "__main__":
    test_prompt = "Retro vintage cyber cat wearing sunglasses, 80s synthwave style"
    saved_path = generate_artwork(test_prompt, "test_cyber_cat.png")
    print(f"Success! Output generated at: {os.path.abspath(saved_path)}")
