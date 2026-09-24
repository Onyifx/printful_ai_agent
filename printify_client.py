import os
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

PRINTIFY_API_TOKEN = os.getenv("PRINTIFY_TOKEN")
PRINTIFY_SHOP_ID = os.getenv("SHOP_ID")

HEADERS = {
    "Authorization": f"Bearer {PRINTIFY_API_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "POD-Automation-Agent/1.0"
}

BASE_URL = "https://api.printify.com/v1"

def get_shop_id():
    """Retrieves or returns the configured Printify Shop ID."""
    if PRINTIFY_SHOP_ID:
        return PRINTIFY_SHOP_ID
    
    url = f"{BASE_URL}/shops.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        shops = res.json()
        if shops:
            return str(shops[0]['id'])
    raise Exception(f"Failed to fetch Printify Shop ID: {res.text}")

def upload_artwork(file_path: str, retries: int = 4, delay: int = 10) -> str:
    """
    Uploads an image file to Printify Media Library with extended timeout and retry logic.
    Endpoint: POST /v1/uploads/images.json
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
            # Extended timeout to 120 seconds for large 3000x3000px payloads
            res = requests.post(url, json=payload, headers=HEADERS, timeout=120)
            if res.status_code in [200, 201]:
                image_data = res.json()
                print(f"✅ Upload successful! Media Image ID: {image_data.get('id')}")
                return image_data.get('id')
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

def get_valid_blueprint_config(blueprint_id: int = 6, max_variants: int = 4):
    """
    Dynamically fetches an active print provider and valid variant IDs 
    handling both list and dict API response formats safely.
    """
    # Step 1: Get available print providers for this blueprint
    providers_url = f"{BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers.json"
    res = requests.get(providers_url, headers=HEADERS)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch print providers for blueprint {blueprint_id}: {res.text}")
    
    providers_data = res.json()
    
    # Safely handle whether the API returns a list directly or a dictionary
    providers = providers_data if isinstance(providers_data, list) else providers_data.get("print_providers", [])
    
    if not providers:
        raise Exception(f"No active print providers found for blueprint {blueprint_id}")
    
    # Pick the first available print provider from the list
    print_provider_id = providers[0]["id"]
    print(f"ℹ️ Selected Print Provider ID: {print_provider_id} for Blueprint {blueprint_id}")

    # Step 2: Get active variants for this provider & blueprint
    variants_url = f"{BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
    res = requests.get(variants_url, headers=HEADERS)
    if res.status_code == 200:
        variants_data = res.json()
        
        # Safely handle variants response format as well
        variants = variants_data if isinstance(variants_data, list) else variants_data.get("variants", [])
        
        if variants:
            variant_ids = [v["id"] for v in variants[:max_variants]]
            return print_provider_id, variant_ids
            
    raise Exception(f"Failed to fetch variants for blueprint {blueprint_id} with provider {print_provider_id}: {res.text}")

def create_tshirt_product(shop_id: str, title: str, description: str, image_id: str) -> dict:
    """Creates a print-on-demand t-shirt product draft on Printify using live configuration."""
    url = f"{BASE_URL}/shops/{shop_id}/products.json"

    blueprint_id = 6  # Gildan 5000

    # Dynamically fetch valid print provider and variant IDs
    print_provider_id, variant_ids = get_valid_blueprint_config(blueprint_id)
    variants_payload = [{"id": v_id, "price": 2499, "is_enabled": True} for v_id in variant_ids]

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
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1.0,
                                "angle": 0
                            }
                        ]
                    }
                ]
            }
        ]
    }

    res = requests.post(url, json=payload, headers=HEADERS)
    if res.status_code in [200, 201]:
        return res.json()
    raise Exception(f"Failed to create product on Printify: {res.text}")