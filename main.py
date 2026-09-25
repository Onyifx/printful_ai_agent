import os
import sys
import json
import time
from dotenv import load_dotenv

# Import official Groq SDK
from groq import Groq

# Import trend discovery module
from trend_discovery import fetch_trending_niches

# Import visual graphic image generator
from graphic_engine import generate_artwork

# Import dual-product Printify client
from printify_client import get_shop_id, upload_artwork, create_matching_set_products

# Import SMTP notification module
from notifier import send_email_report

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY is missing from your environment variables.")

# Initialize the Groq Client
client = Groq(api_key=GROQ_API_KEY)

# System prompt defining streetwear matching set criteria
STREETWEAR_PROMPT_SYSTEM = """
You are an expert Streetwear Creative Director and E-Commerce Merchandise Strategist specializing in high-converting matching two-piece outfit sets ("Up and Down" sets) for platforms like Etsy, Temu, and TikTok Shop.
"""

def safe_send_email(subject: str, html_content: str):
    """Helper function to safely dispatch email notifications."""
    try:
        send_email_report(subject, html_content)
    except Exception as e:
        print(f"⚠️ Email notification skipped/failed: {e}")

def generate_set_intelligence(niche_topic: str) -> dict:
    """
    Executes a Multi-Model Consensus Pipeline:
    1. Primary Creator Model (GPT-OSS 120B) drafts artwork drawing prompts and dual-product listing metadata.
    2. Auditor Model (Qwen 27B) optimizes artwork prompt and SEO tags for maximum conversions.
    """
    print(f"⚡ [Groq AI Consensus Engine] Initializing matching set workflow for: '{niche_topic}'...")
    
    creator_model = "openai/gpt-oss-120b"
    auditor_model = "qwen/qwen3.8-27b"
    
    system_instruction_creator = (
        f"{STREETWEAR_PROMPT_SYSTEM}\n\n"
        "Analyze the provided niche topic and produce an end-to-end strategy for a matching 2-piece streetwear outfit set (Top + Shorts/Joggers):\n"
        "1. image_prompt: A rich, vivid drawing prompt for an AI image generator to draw bold graphic artwork (e.g., 'Vintage 90s racing motorcycle illustration, detailed biker character, cyber retro streetwear graphic').\n"
        "2. top_garment_type: Exactly one of ['oversized_tee', 'standard_tee', 'hoodie', 'sweatshirt'].\n"
        "3. bottom_garment_type: Exactly one of ['sweatshorts', 'joggers'].\n"
        "4. top_title: SEO-optimized product title for the top item.\n"
        "5. bottom_title: SEO-optimized product title for the matching bottom item.\n"
        "6. description: Engaging product copy describing the set aesthetic, comfort, and streetwear fit.\n"
        "7. tags: Array of exactly 13 search tags for Etsy/Shopify.\n"
        "You MUST output valid JSON strictly without conversational text."
    )
    
    prompt_text = f"""
    Perform a complete matching streetwear set breakdown for the trend niche: "{niche_topic}".
    
    Return a JSON object containing:
    1. "image_prompt": Detailed visual artwork prompt.
    2. "top_garment_type": Garment choice for the top.
    3. "bottom_garment_type": Garment choice for the bottom.
    4. "top_title": Product title for the top item.
    5. "bottom_title": Product title for the bottom item.
    6. "description": Product copy.
    7. "tags": Exactly 13 search tags as an array of strings.
    8. "target_audience": Primary demographic profile.
    9. "suggested_set_price": Total retail price for the set (e.g., 64.99).
    """

    # Step 1: Creator Phase
    print(f"🤖 [Creator Agent - {creator_model}] Drafting initial product package & artwork prompt...")
    try:
        response_creator = client.chat.completions.create(
            model=creator_model,
            messages=[
                {"role": "system", "content": system_instruction_creator},
                {"role": "user", "content": prompt_text}
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
            temperature=0.7,
        )
        draft_intel = json.loads(response_creator.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ Creator model failed: {e}. Raising error...")
        raise e

    # Step 2: Auditor Phase
    print(f"🧐 [Auditor Agent - {auditor_model}] Reviewing and refining artwork prompts and listing metadata...")
    
    audit_instruction = (
        f"{STREETWEAR_PROMPT_SYSTEM}\n\n"
        "Review and enhance the provided JSON package for a matching streetwear set. "
        "Ensure image_prompt describes bold, high-contrast streetwear artwork clearly. "
        "Verify top_garment_type is one of ['oversized_tee', 'standard_tee', 'hoodie', 'sweatshirt'] and "
        "bottom_garment_type is one of ['sweatshorts', 'joggers']. "
        "Ensure exactly 13 SEO search tags. Return the final valid JSON object maintaining the exact same keys."
    )
    
    audit_payload = f"Here is the draft JSON package to audit:\n{json.dumps(draft_intel, indent=2)}"

    try:
        response_auditor = client.chat.completions.create(
            model=auditor_model,
            messages=[
                {"role": "system", "content": audit_instruction},
                {"role": "user", "content": audit_payload}
            ],
            response_format={"type": "json_object"},
            max_tokens=1200,
            temperature=0.4,
        )
        final_intel = json.loads(response_auditor.choices[0].message.content)
        print("✅ Multi-model consensus reached: Set intelligence successfully audited!")
        return final_intel
    except Exception as e:
        print(f"⚠️ Auditor model review skipped due to error: {e}. Using creator draft.")
        return draft_intel

def run_pipeline(niche_topic: str):
    start_time = time.time()
    print("\n==================================================")
    print(f"🚀 LAUNCHING AUTOMATED 'UP & DOWN' SET PIPELINE: '{niche_topic}'")
    print("==================================================\n")
    
    try:
        # 1. AI Concept & Multi-Model Intelligence Generation
        intel = generate_set_intelligence(niche_topic)
        
        image_prompt = intel.get("image_prompt", f"Bold streetwear illustration of {niche_topic}")
        top_garment = intel.get("top_garment_type", "oversized_tee").lower()
        bottom_garment = intel.get("bottom_garment_type", "sweatshorts").lower()

        print("\n--------------------------------------------------")
        print(f"💡 GROQ CONSENSUS INTELLIGENCE OUTPUT:")
        print(f"  [Artwork Prompt]    : {image_prompt}")
        print(f"  [Top Garment]       : {top_garment.upper()}")
        print(f"  [Bottom Garment]    : {bottom_garment.upper()}")
        print(f"  [Top Title]         : {intel.get('top_title')}")
        print(f"  [Bottom Title]      : {intel.get('bottom_title')}")
        print(f"🏷️ SEO Tags ({len(intel.get('tags', []))}): {', '.join(intel.get('tags', []))}")
        print("--------------------------------------------------\n")

        # 2. Artwork Generation & Processing via graphic_engine
        filename = f"set_{niche_topic.lower().replace(' ', '_')}.png"
        image_path = generate_artwork(concept_prompt=image_prompt, output_filename=filename)
        
        # 3. Printify Shop Connection
        shop_id = get_shop_id()
        print(f"🔑 Connected to Printify Shop ID: {shop_id}")
        
        # 4. Artwork Upload (Shared between top and bottom)
        image_id = upload_artwork(image_path)
        
        # 5. Dual-Product Creation (Top + Bottom Set)
        set_products = create_matching_set_products(
            shop_id=shop_id,
            top_title=intel.get("top_title", f"Custom {niche_topic} Streetwear Top"),
            bottom_title=intel.get("bottom_title", f"Custom {niche_topic} Matching Bottoms"),
            description=intel.get("description", "High quality streetwear piece."),
            image_id=image_id,
            tags=intel.get("tags"),
            top_garment=top_garment,
            bottom_garment=bottom_garment
        )
        
        elapsed = time.time() - start_time
        print("\n==================================================")
        print("🎉 MATCHING OUTFIT SET PUBLISHED SUCCESSFULLY!")
        print(f"⏱️ Total Execution Time: {elapsed:.2f} seconds")
        print(f"👕 Top Product ID    : {set_products['top'].get('id')}")
        print(f"🩳 Bottom Product ID : {set_products['bottom'].get('id')}")
        print("==================================================")

        # 6. Dispatch Success Email Report
        success_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #f9fff9;">
            <h2 style="color: #27ae60;">🎉 Matching 'Up & Down' Streetwear Set Published!</h2>
            <p>Your autonomous agent discovered a live trend, generated detailed visual artwork, and created a matching 2-piece outfit set on Printify.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <ul>
                <li><b>Discovered Trend:</b> {niche_topic}</li>
                <li><b>Artwork Prompt:</b> {image_prompt}</li>
                <li><b>Top Product Title:</b> {set_products['top'].get('title')} (ID: {set_products['top'].get('id')})</li>
                <li><b>Bottom Product Title:</b> {set_products['bottom'].get('title')} (ID: {set_products['bottom'].get('id')})</li>
                <li><b>Total Execution Time:</b> {elapsed:.2f} seconds</li>
            </ul>
        </div>
        """
        safe_send_email(f"🚀 Autonomous POD Success: Matching Set for {niche_topic}", success_html)

    except Exception as e:
        elapsed = time.time() - start_time
        error_message = str(e)
        print(f"\n❌ Pipeline failed with error: {error_message}")
        
        failure_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ffccd5; border-radius: 8px; background-color: #fff5f5;">
            <h2 style="color: #c0392b;">❌ Matching Set Pipeline Failed</h2>
            <p>The autonomous agent encountered an error during execution.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <ul>
                <li><b>Niche Topic:</b> {niche_topic}</li>
                <li><b>Error Details:</b> <code style="color: #c0392b;">{error_message}</code></li>
                <li><b>Execution Time:</b> {elapsed:.2f} seconds</li>
            </ul>
        </div>
        """
        safe_send_email(f"⚠️ Pipeline Failure: {niche_topic}", failure_html)
        raise e

if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        print("🌐 No custom topic passed. Triggering Live Web Trend Discovery...")
        topic = fetch_trending_niches()
        
    run_pipeline(topic)
