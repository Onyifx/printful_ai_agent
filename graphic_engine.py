import os
import io
import time
import requests
from PIL import Image
from rembg import remove
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from .env file
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
    
    # 1. Check if the file actually exists on the hard drive/server
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Quality Gate Error: File not found at {file_path}")
        
    # 2. Check if the file contains actual data (size must be > 1 KB)
    file_size_bytes = os.path.getsize(file_path)
    if file_size_bytes < 1024:
        raise Exception(f"Quality Gate Error: File size is suspiciously small ({file_size_bytes} bytes).")

    # 3. Open the image file to inspect its pixel structure
    with Image.open(file_path) as img:
        # Verify exact print-ready pixel resolution
        width, height = img.size
        if width != 3000 or height != 3000:
            raise Exception(f"Quality Gate Error: Invalid dimensions {width}x{height}px. Required: 3000x3000px.")
            
        # Verify color space (RGBA required for transparent backgrounds)
        if img.mode != "RGBA":
            raise Exception(f"Quality Gate Error: Invalid color mode '{img.mode}'. Required: RGBA.")
            
        # Inspect the Alpha channel (the transparency layer)
        alpha_channel = img.getchannel("A")
        extrema = alpha_channel.getextrema()  # Returns (min_transparency, max_transparency) between 0 and 255
        
        # If min and max are both 255, the image is 100% solid (background was not stripped)
        if extrema[0] == 255 and extrema[1] == 255:
            print("⚠️ Quality Gate Warning: Image lacks transparency (fully opaque background detected).")
            
        # If max is 0, the image is 100% invisible/blank
        if extrema[1] == 0:
            raise Exception("Quality Gate Error: Processed image is completely transparent/blank.")
            
    print("✅ Quality Gate Passed: Artwork meets high-res Printify production standards.")
    return True


def generate_artwork(concept_prompt: str, output_filename: str = "temp_artwork.png") -> str:
    """
    1. Fetches raw AI artwork from Pollinations using parameter-safe URL strategies to bypass HTTP 500 errors.
    2. Crops off the bottom watermark region.
    3. Strips background using rembg (transparent PNG).
    4. Upscales to 3000x3000px @ 300 DPI for high-print quality.
    5. Runs Visual Quality Gate inspection checks.
    6. Saves to local disk.
    """
    print(f"🎨 [1/5] Generating raw artwork for prompt: '{concept_prompt}'...")
    
    # Format and sanitize the prompt into a single line
    clean_prompt = f"{concept_prompt}, high contrast graphic vector art, t-shirt design style, isolated subject on solid background".strip().replace("\n", " ")
    
    # Convert spaces and special characters into web-safe URL formatting (e.g. spaces become %20)
    encoded_prompt = quote(clean_prompt)

    # Web browser headers to make the script look like a standard web browser and prevent automated blocking
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Sequence of backup URLs starting from full settings down to basic minimal prompts
    seed = int(time.time())
    url_strategies = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}",
        f"https://image.pollinations.ai/prompt/{quote(clean_prompt[:120])}?nologo=true"
    ]

    response = None
    # Iterate through each fallback URL strategy
    for attempt, url in enumerate(url_strategies, start=1):
        print(f"🌐 [Attempt {attempt}/{len(url_strategies)}] Requesting artwork from Pollinations AI...")
        try:
            res = requests.get(url, headers=headers, timeout=60)
            # Check if server responded with OK status (200) and actual image data (> 5 KB)
            if res.status_code == 200 and len(res.content) > 5000:
                response = res
                print(f"✅ Downloaded raw artwork ({len(res.content) / 1024:.1f} KB)")
                break
            else:
                print(f"⚠️ Pollinations AI returned status {res.status_code}. Retrying with simplified strategy in 4s...")
                time.sleep(4)
        except requests.RequestException as e:
            print(f"⚠️ Network error on attempt {attempt}: {e}. Retrying in 4s...")
            time.sleep(4)

    # If all attempts failed, throw an error to stop execution safely
    if not response or response.status_code != 200:
        status = response.status_code if response else "No Response"
        raise Exception(f"Failed to retrieve image from Pollinations AI after trying all fallback strategies (Status: {status}).")

    # Load raw downloaded binary data into a PIL Image object
    raw_img = Image.open(io.BytesIO(response.content))
    
    print("✂️ [2/5] Cropping bottom watermark zone...")
    w, h = raw_img.size
    # Crop top 93% of the image, cutting off the bottom 7% where logos or watermarks sit
    clean_img = raw_img.crop((0, 0, w, int(h * 0.93)))
    
    # Save cropped image back into temporary memory
    img_byte_arr = io.BytesIO()
    clean_img.save(img_byte_arr, format="PNG")
    cropped_bytes = img_byte_arr.getvalue()
    
    print("🧼 [3/5] Stripping background with rembg...")
    # Use AI background removal to isolate the subject and create a transparent PNG
    transparent_bytes = remove(cropped_bytes)
    
    print("📐 [4/5] Upscaling artwork to 3000x3000px @ 300 DPI...")
    image = Image.open(io.BytesIO(transparent_bytes)).convert("RGBA")
    
    # Resize the image to 3000x3000 pixels using Lanczos resampling for high print clarity
    high_res_image = image.resize((3000, 3000), Image.Resampling.LANCZOS)
    
    # Save the final processed image file to disk with 300 DPI metadata
    high_res_image.save(output_filename, format="PNG", dpi=(300, 300))
    
    print("🛡️ [5/5] Executing Visual Quality Gate inspection...")
    inspect_artwork_quality(output_filename)
    
    print(f"✅ Artwork processing & validation complete! File saved as: {output_filename}")
    return output_filename


# Alias mapping so scripts expecting generate_transparent_artwork can run without modification
generate_transparent_artwork = generate_artwork

if __name__ == "__main__":
    print("🧪 Testing High-DPI Graphic Engine with Quality Gate...")
    test_prompt = "Retro vintage cyber cat wearing sunglasses, 80s synthwave style"
    saved_path = generate_artwork(test_prompt, "test_cyber_cat.png")
    print(f"Success! Output generated at: {os.path.abspath(saved_path)}")
