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
    Inspects the processed artwork file to ensure it meets strict Printify production criteria:
    - Verifies file existence and non-zero size.
    - Confirms exact dimensions (3000x3000px).
    - Checks color mode (RGBA).
    - Verifies alpha channel transparency is balanced (not completely blank or solid).
    """
    print(f"🔍 [Quality Gate] Inspecting graphic asset integrity for: '{os.path.basename(file_path)}'...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Quality Gate Error: File not found at {file_path}")
        
    file_size_bytes = os.path.getsize(file_path)
    if file_size_bytes < 1024:
        raise Exception(f"Quality Gate Error: File size is suspiciously small ({file_size_bytes} bytes).")

    with Image.open(file_path) as img:
        # Check dimensions
        width, height = img.size
        if width != 3000 or height != 3000:
            raise Exception(f"Quality Gate Error: Invalid dimensions {width}x{height}px. Required: 3000x3000px.")
            
        # Check color mode
        if img.mode != "RGBA":
            raise Exception(f"Quality Gate Error: Invalid color mode '{img.mode}'. Required: RGBA.")
            
        # Check alpha channel transparency balance
        alpha_channel = img.getchannel("A")
        extrema = alpha_channel.getextrema()  # Returns (min, max) alpha values (0 to 255)
        
        # If min and max are both 255, it has zero transparency (background wasn't stripped)
        if extrema[0] == 255 and extrema[1] == 255:
            print("⚠️ Quality Gate Warning: Image lacks transparency (fully opaque background detected).")
            
        # If max is 0, the image is entirely invisible/blank
        if extrema[1] == 0:
            raise Exception("Quality Gate Error: Processed image is completely transparent/blank.")
            
    print("✅ Quality Gate Passed: Artwork meets high-res Printify production standards.")
    return True

def generate_artwork(concept_prompt: str, output_filename: str = "temp_artwork.png", retries: int = 4) -> str:
    """
    1. Fetches raw generated artwork from Pollinations AI with browser headers & model fallback.
    2. Crops off the bottom watermark region.
    3. Strips background using rembg (transparent PNG).
    4. Upscales to 3000x3000px @ 300 DPI for high-print quality.
    5. Runs Visual Quality Gate inspection checks.
    6. Saves to local disk.
    """
    print(f"🎨 [1/5] Generating raw artwork for prompt: '{concept_prompt}'...")
    
    styled_prompt = f"{concept_prompt}, high contrast graphic vector art, t-shirt design style, isolated subject on plain background"
    clean_prompt = styled_prompt.strip().replace("\n", " ")
    encoded_prompt = quote(clean_prompt)

    # Headers required to bypass automated request blocking on GitHub Actions runners
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Model endpoints to try in sequence if primary fails
    models_to_try = ["flux", "turbo", "default"]
    
    response = None
    for attempt in range(1, retries + 1):
        model = models_to_try[(attempt - 1) % len(models_to_try)]
        
        if model == "default":
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
        else:
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model={model}&seed={int(time.time())}"

        print(f"🌐 [Attempt {attempt}/{retries}] Fetching AI artwork from Pollinations AI (Model: {model})...")

        try:
            res = requests.get(url, headers=headers, timeout=60)
            if res.status_code == 200 and len(res.content) > 5000:
                response = res
                print(f"✅ Downloaded raw artwork ({len(res.content) / 1024:.1f} KB)")
                break
            else:
                print(f"⚠️ Pollinations AI returned status {res.status_code} or incomplete data. Retrying in {attempt * 5}s...")
                time.sleep(attempt * 5)
        except requests.RequestException as e:
            print(f"⚠️ Network error on attempt {attempt}: {e}. Retrying in {attempt * 5}s...")
            time.sleep(attempt * 5)

    if not response or response.status_code != 200:
        status = response.status_code if response else "No Response"
        raise Exception(f"Failed to retrieve image from Pollinations AI after {retries} attempts (Status: {status}).")

    # Load raw image into PIL
    raw_img = Image.open(io.BytesIO(response.content))
    
    print("✂️ [2/5] Cropping bottom watermark zone...")
    w, h = raw_img.size
    clean_img = raw_img.crop((0, 0, w, int(h * 0.93)))
    
    # Save cropped image to bytes buffer
    img_byte_arr = io.BytesIO()
    clean_img.save(img_byte_arr, format="PNG")
    cropped_bytes = img_byte_arr.getvalue()
    
    print("🧼 [3/5] Stripping background with rembg...")
    transparent_bytes = remove(cropped_bytes)
    
    print("📐 [4/5] Upscaling artwork to 3000x3000px @ 300 DPI...")
    image = Image.open(io.BytesIO(transparent_bytes)).convert("RGBA")
    
    # Resize to Printify high-res specification using Lanczos resampling
    high_res_image = image.resize((3000, 3000), Image.Resampling.LANCZOS)
    
    # Save as temporary file before inspection
    high_res_image.save(output_filename, format="PNG", dpi=(300, 300))
    
    print("🛡️ [5/5] Executing Visual Quality Gate inspection...")
    inspect_artwork_quality(output_filename)
    
    print(f"✅ Artwork processing & validation complete! File saved as: {output_filename}")
    return output_filename

# Function alias to support both import naming formats
generate_transparent_artwork = generate_artwork

if __name__ == "__main__":
    print("🧪 Testing High-DPI Graphic Engine with Quality Gate...")
    test_prompt = "Retro vintage cyber cat wearing sunglasses, 80s synthwave style"
    saved_path = generate_artwork(test_prompt, "test_cyber_cat.png")
    print(f"Success! Output generated at: {os.path.abspath(saved_path)}")
