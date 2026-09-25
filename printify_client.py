import os
import time
import base64
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_URL = "https://api.printify.com/v1"

def get_clean_api_key() -> str:
    """
    Retrieves and sanitizes the Printify API token/key by stripping newlines, 
    carriage returns, spaces, and quotes that cause HTTP header errors.
    Supports both PRINTIFY_TOKEN and PRINTIFY_API_KEY environment variables.
    """
    key = os.getenv("PRINTIFY_TOKEN") or os.getenv("PRINTIFY_API_KEY", "")
    if not key:
        raise ValueError("❌ PRINTIFY_TOKEN or PRINTIFY_API_KEY is missing from environment variables.")
    return key.strip().replace("\n", "").replace("\r", "").strip('"').strip("'")

def get_clean_shop_id() -> str:
    """Retrieves and sanitizes the configured Printify Shop ID if present."""
    shop_id = os.getenv("SHOP_ID") or os.getenv("PRINTIFY_SHOP_ID", "")
    return shop_id.strip().replace("\n", "").replace("\r", "").strip('"').strip("'")

def get_headers() -> dict:
    """Builds sanitized HTTP headers dynamically for Printify API requests."""
    return {
        "Authorization": f"Bearer {get_clean_api_key()}",
        "Content-Type": "application/json",
        "User-Agent": "POD-Automation-Agent/1.0"
    }

def get_shop_id() -> str:
    """Retrieves configured Shop ID or dynamically fetches the first active shop from Printify."""
    shop_id = get_clean_shop_id()
    if shop_id:
        return shop_id
    
    url = f"{BASE_URL}/shops.json"
    res = requests.get(url, headers=get_headers(), timeout=30)
    if res.status_code == 200:
        shops = res.json()
        if shops:
            return str(shops[0]['id'])
    raise Exception(f"Failed to fetch Printify Shop ID: {res.status_code} - {res.text}")

def upload_artwork(file_path: str, retries: int = 4, delay: int = 10) -> str:
    """
    Encodes artwork as base64 and uploads it to the Printify Media Library
    with retry logic, dynamic headers, and extended timeout for large files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Artwork file not found at path: {file_path}")

    filename = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📤 Uploading artwork '{filename}' ({file_size_mb:.2f} MB) to Printify Media Library...")

    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        "file_name": filename,
        "contents": encoded_string
    }

    url = f"{BASE_URL}/uploads/images.json"

    for attempt in range(1, retries + 1):
        try:
            # Extended timeout to 120 seconds for high-resolution graphics
            res = requests.post(url, json=payload, headers=get_headers(), timeout=120)
            if res.status_code in [200, 201]:
                image_data = res.json()
                print(f"✅ Upload successful! Media Image ID: {image_data.get('id')}")
                return str(image_data.get('id'))
            elif res.status_code in [502, 503, 504]:
                print(f"⚠️ Printify API returned server error {res.status_code}. Retrying in {delay} seconds (Attempt {attempt}/{retries})...")
                time.sleep(delay)
                delay *= 2
            else:
                raise Exception(f"Upload failed with status {res.status_code}: {res.text}")
        except requests.RequestException as e:
            print(f"⚠️ Network error during upload: {e}. Retrying in {delay} seconds (Attempt {attempt}/{retries})...")
            time.sleep(delay)
            delay *= 2

    raise Exception(f"Failed to upload image to Printify after {retries} attempts.")

def get_valid_blueprint_config(blueprint_id: int = 12, max_variants: int = 4):
    """
    Dynamically fetches an active print provider and valid variant IDs for the selected blueprint.
    Handles both list and dictionary API response formats safely.
    """
    providers_url = f"{BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers.json"
    res = requests.get(providers_url, headers=get_headers(), timeout=30)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch print providers for blueprint {blueprint_id}: {res.text}")
    
    providers_data = res.json()
    providers = providers_data if isinstance(providers_data, list) else providers_data.get("print_providers", [])
    
    if not providers:
        raise Exception(f"No active print providers found for blueprint {blueprint_id}")
    
    print_provider_id = providers[0]["id"]
    print(f"ℹ️ Selected Print Provider ID: {print_provider_id} for Blueprint {blueprint_id}")

    variants_url = f"{BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
    res = requests.get(variants_url, headers=get_headers(), timeout=30)
    if res.status_code == 200:
        variants_data = res.json()
        variants = variants_data if isinstance(variants_data, list) else variants_data.get("variants", [])
        
        if variants:
            variant_ids = [v["id"] for v in variants[:max_variants]]
            return print_provider_id, variant_ids
            
    raise Exception(f"Failed to fetch variants for blueprint {blueprint_id} with provider {print_provider_id}: {res.text}")

def create_tshirt_product(shop_id: str, title: str, description: str, image_id: str) -> dict:
    """
    Creates a print-on-demand streetwear t-shirt draft on Printify using premium 
    Bella + Canvas 3001 blanks and 80% full-chest upper placement settings.
    """
    print(f"👕 Creating T-Shirt product in Printify Shop ID '{shop_id}'...")
    url = f"{BASE_URL}/shops/{shop_id}/products.json"

    # Blueprint 12 = Bella + Canvas 3001 Unisex Jersey Short Sleeve Tee
    # (To switch to Comfort Colors 1717 Vintage Tee, change blueprint_id to 382)
    blueprint_id = 12

    # Dynamically fetch valid print provider and variant IDs for Blueprint 12
    print_provider_id, variant_ids = get_valid_blueprint_config(blueprint_id)
    variants_payload = [{"id": v_id, "price": 2699, "is_enabled": True} for v_id in variant_ids]

    payload = {
        "title": title,
        "description": description,
        "blueprint_id": blueprint_id,
        "print_provider_id": print_provider_id,
        "variants": variants_payload,
        "print_areas": [
            {
                "variant_ids": variant_ids,
                "placeholders": [
                    {
                        "position": "front",
                        "images": [
                            {
                                "id": image_id,
                                "x": 0.50,      # Perfectly centered horizontally
                                "y": 0.28,      # Positioned high on the upper chest
                                "scale": 0.80,  # Scaled to 80% full-chest width
                                "angle": 0
                            }
                        ]
                    }
                ]
            }
        ]
    }

    res = requests.post(url, json=payload, headers=get_headers(), timeout=30)
    if res.status_code in [200, 201]:
        product_data = res.json()
        print(f"🎉 Product created successfully! Product ID: {product_data.get('id')}")
        return product_data
    raise Exception(f"Failed to create product on Printify: {res.text}")
