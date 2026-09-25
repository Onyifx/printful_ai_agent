import os
import time
import base64
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_URL = "https://api.printify.com/v1"

# Extended Printify Garment Catalog Mapping (Tops + Bottoms)
GARMENT_CATALOG = {
    # TOPS
    "standard_tee": {
        "blueprint_id": 12,       # Bella + Canvas 3001 Unisex Tee
        "default_price": 2999,
        "name": "Bella + Canvas 3001 Unisex Tee",
        "category": "top"
    },
    "oversized_tee": {
        "blueprint_id": 706,      # Comfort Colors 1717 Heavyweight Vintage Tee
        "default_price": 3499,
        "name": "Comfort Colors 1717 Heavyweight Tee",
        "category": "top"
    },
    "hoodie": {
        "blueprint_id": 77,       # Gildan 18500 Heavy Blend Hoodie
        "default_price": 4999,
        "name": "Gildan 18500 Heavy Blend Hoodie",
        "category": "top"
    },
    "sweatshirt": {
        "blueprint_id": 49,       # Gildan 18000 Crewneck Sweatshirt
        "default_price": 4299,
        "name": "Gildan 18000 Crewneck Sweatshirt",
        "category": "top"
    },
    # BOTTOMS
    "sweatshorts": {
        "blueprint_id": 804,      # Streetwear Fleece Shorts
        "default_price": 3499,
        "name": "Streetwear Fleece Sweatshorts",
        "category": "bottom"
    },
    "joggers": {
        "blueprint_id": 1398,     # Gildan Unisex Sweatpants
        "default_price": 4499,
        "name": "Gildan Unisex Sweatpants",
        "category": "bottom"
    }
}

def get_clean_api_key() -> str:
    """Retrieves and sanitizes the Printify API token/key."""
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
    """Encodes artwork as base64 and uploads it to the Printify Media Library."""
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
            res = requests.post(url, json=payload, headers=get_headers(), timeout=120)
            if res.status_code in [200, 201]:
                image_data = res.json()
                print(f"✅ Upload successful! Media Image ID: {image_data.get('id')}")
                return str(image_data.get('id'))
            elif res.status_code in [502, 503, 504]:
                print(f"⚠️ Printify API server error {res.status_code}. Retrying in {delay} seconds (Attempt {attempt}/{retries})...")
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
    """Dynamically parses exact print provider and valid placeholder positions from the variant API array."""
    # 1. Fetch Print Providers
    providers_url = f"{BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers.json"
    res = requests.get(providers_url, headers=get_headers(), timeout=30)
    
    if res.status_code == 404:
        print(f"⚠️ Warning: Blueprint {blueprint_id} not found. Falling back to 1398 (Gildan Sweatpants)...")
        blueprint_id = 1398
        res = requests.get(f"{BASE_URL}/catalog/blueprints/1398/print_providers.json", headers=get_headers(), timeout=30)

    if res.status_code != 200:
        raise Exception(f"Failed to fetch print providers for blueprint {blueprint_id}: {res.text}")
    
    providers_data = res.json()
    providers = providers_data if isinstance(providers_data, list) else providers_data.get("print_providers", [])
    
    if not providers:
        raise Exception(f"No active print providers found for blueprint {blueprint_id}")
    
    print_provider_id = providers[0]["id"]

    # 2. Fetch specific variant IDs AND extract EXACT valid placeholders from the variant data
    variants_url = f"{BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
    res_variants = requests.get(variants_url, headers=get_headers(), timeout=30)
    
    if res_variants.status_code == 200:
        variants_data = res_variants.json()
        variants = variants_data if isinstance(variants_data, list) else variants_data.get("variants", [])
        
        placeholder_position = "front" # Ultimate Fallback
        
        if variants:
            # Extract placeholders directly from what the provider supports for this blueprint
            first_variant = variants[0]
            placeholders = first_variant.get("placeholders", [])
            
            valid_positions = [p.get("position") for p in placeholders if "position" in p]
            
            if valid_positions:
                # If bottom garment, look for any leg/thigh/left/right print position
                if blueprint_id in [1398, 804]:
                    leg_positions = [p for p in valid_positions if "leg" in p.lower() or "left" in p.lower() or "right" in p.lower()]
                    placeholder_position = leg_positions[0] if leg_positions else valid_positions[0]
                else:
                    # Top garments will naturally pull "front" or whatever the first valid tag is
                    placeholder_position = valid_positions[0]
            
            print(f"🔧 Found Print Provider {print_provider_id}. API strictly locked to placeholder: '{placeholder_position}'")

            # Filter active variants
            active_variants = [v for v in variants if v.get("is_enabled", True)]
            if not active_variants:
                active_variants = variants
                
            variant_ids = [v["id"] for v in active_variants[:max_variants]]
            return print_provider_id, variant_ids, placeholder_position
            
    raise Exception(f"Failed to fetch variants for blueprint {blueprint_id} with provider {print_provider_id}: {res_variants.text}")

def create_single_product(shop_id: str, title: str, description: str, image_id: str, tags: list, garment_type: str) -> dict:
    """Internal helper to create a single product on Printify with dynamic print positioning."""
    garment_info = GARMENT_CATALOG.get(garment_type.lower(), GARMENT_CATALOG["standard_tee"])
    blueprint_id = garment_info["blueprint_id"]
    default_price = garment_info["default_price"]
    is_bottom = garment_info.get("category") == "bottom"

    print(f"👕 Creating apparel product '{garment_info['name']}' in Printify Shop ID '{shop_id}'...")
    url = f"{BASE_URL}/shops/{shop_id}/products.json"

    tags = (tags or ["streetwear", "graphic tee", "vintage fashion"])[:13]
    
    # Retrieves strict, dynamic configuration directly from Printify's catalog
    print_provider_id, variant_ids, placeholder_position = get_valid_blueprint_config(blueprint_id)
    variants_payload = [{"id": v_id, "price": default_price, "is_enabled": True} for v_id in variant_ids]

    pos_y = 0.40 if is_bottom else 0.28
    pos_x = 0.35 if is_bottom else 0.50
    scale = 0.45 if is_bottom else 0.80

    payload = {
        "title": title,
        "description": description,
        "blueprint_id": blueprint_id,
        "print_provider_id": print_provider_id,
        "variants": variants_payload,
        "tags": tags,
        "print_areas": [
            {
                "variant_ids": variant_ids,
                "placeholders": [
                    {
                        "position": placeholder_position,
                        "images": [
                            {
                                "id": image_id,
                                "x": pos_x,
                                "y": pos_y,
                                "scale": scale,
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

def create_matching_set_products(shop_id: str, top_title: str, bottom_title: str, description: str, image_id: str, tags: list, top_garment: str = "oversized_tee", bottom_garment: str = "sweatshorts") -> dict:
    """
    Creates both the Top and Bottom products on Printify in a single execution,
    forming a complete, coordinated 'Up and Down' streetwear set.
    """
    print("\n🔥 [Printify Dual Creation] Building matching 'Up & Down' apparel set...")
    
    top_product = create_single_product(
        shop_id=shop_id,
        title=top_title,
        description=f"{description}\n\n• Part of a matching two-piece streetwear outfit set.",
        image_id=image_id,
        tags=tags,
        garment_type=top_garment
    )
    
    bottom_product = create_single_product(
        shop_id=shop_id,
        title=bottom_title,
        description=f"{description}\n\n• Matching streetwear bottoms designed to pair perfectly with the coordinate top.",
        image_id=image_id,
        tags=tags,
        garment_type=bottom_garment
    )

    return {
        "top": top_product,
        "bottom": bottom_product
    }

# Backward compatibility alias
create_tshirt_product = lambda shop_id, title, description, image_id, tags=None, garment_type="standard_tee": create_single_product(shop_id, title, description, image_id, tags, garment_type)
