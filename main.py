import os
import sys
import json
import time
from dotenv import load_dotenv

# Import official Groq SDK
from groq import Groq

# Import trend discovery module
from trend_discovery import fetch_trending_niches

# Import graphic engine artwork generator directly
from graphic_engine import generate_artwork

from printify_client import get_shop_id, upload_artwork, create_tshirt_product
from notifier import send_email_report

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY is missing from your environment variables.")

# Initialize the Groq Client
client = Groq(api_key=GROQ_API_KEY)

def safe_send_email(subject: str, html_content: str):
    """
    Helper function to safely dispatch email notifications.
    If email credentials are missing or failing, logs a warning instead of stopping the pipeline.
    """
    try:
        send_email_report(subject, html_content)
    except Exception as e:
        print(f"⚠️ Email notification skipped/failed: {e}")

def generate_listing_intelligence(niche_topic: str) -> dict:
    """
    Executes a Multi-Model Consensus Pipeline:
    1. Primary Creator Model generates the initial e-commerce metadata package.
    2. Auditor/Refiner Model reviews, critiques, and optimizes the content for maximum conversions and SEO.
    """
    print(f"⚡ [Groq AI Consensus Engine] Initializing multi-model workflow for: '{niche_topic}'...")
    
    creator_model = "openai/gpt-oss-120b"
    auditor_model = "qwen/qwen3.8-27b"
    
    system_instruction_creator = (
        "You are an elite E-Commerce Intelligence Engine and Senior Graphic Art Director "
        "specializing in high-volume Print-on-Demand (POD) e-commerce. "
        "Your mission is to generate hyper-optimized listing copy, rank-focused SEO tags, "
        "demographic positioning, and ultra-precise image synthesis prompts optimized for t-shirt graphics. "
        "You MUST output valid JSON only."
    )
    
    prompt_text = f"""
    Perform a complete product concept breakdown for a premium t-shirt listing targeting the niche: "{niche_topic}".
    
    Generate a JSON object containing the following keys:
    1. "title": An SEO-optimized title (between 40-80 characters) packed with high-intent keywords.
    2. "short_description": A 2-sentence catchy sales hook highlighting lifestyle fit and aesthetic appeal.
    3. "description": A full 3-paragraph product description detailing graphic style, comfort, print quality, and gift positioning.
    4. "tags": An array of exactly 13 search tags (comma-separated style keywords) formatted for Etsy/Shopify search engines.
    5. "target_audience": Primary demographic profile (e.g., "Gamers 18-34, Synthwave enthusiasts, Cyberpunk fans").
    6. "recommended_color_palette": Suggested apparel fabric background colors that make the print pop.
    7. "suggested_retail_price": Float value representing the competitive retail price (e.g., 26.99).
    8. "image_prompt": A master graphic prompt engineered for AI image generation. Must specify:
       - Subject and composition
       - Visual style (e.g., vector illustration, high contrast line art, crisp edges)
       - Isolation instruction: "isolated on a plain black background, zero text, vector art style, graphic tee design".
    """

    # Step 1: Creator Phase
    print(f"🤖 [Creator Agent - {creator_model}] Drafting initial product package...")
    try:
        response_creator = client.chat.completions.create(
            model=creator_model,
            messages=[
                {"role": "system", "content": system_instruction_creator},
                {"role": "user", "content": prompt_text}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.7,
        )
        draft_intel = json.loads(response_creator.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ Creator model failed: {e}. Raising error...")
        raise e

    # Step 2: Auditor/Consensus Phase
    print(f"🧐 [Auditor Agent - {auditor_model}] Reviewing and optimizing metadata package for SEO and buyer conversion...")
    
    audit_instruction = (
        "You are a strict Chief Marketing Officer and E-Commerce Quality Assurance Auditor. "
        "Review the provided JSON draft for a Print-on-Demand t-shirt. "
        "Enhance the SEO keywords in the title, tighten the description hooks, ensure exactly 13 high-value search tags, "
        "and polish the image prompt to guarantee pristine visual output. "
        "You MUST return the final, improved version as a valid JSON object maintaining the exact same keys."
    )
    
    audit_payload = f"Here is the draft JSON package to audit and elevate:\n{json.dumps(draft_intel, indent=2)}"

    try:
        response_auditor = client.chat.completions.create(
            model=auditor_model,
            messages=[
                {"role": "system", "content": audit_instruction},
                {"role": "user", "content": audit_payload}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.4,
        )
        final_intel = json.loads(response_auditor.choices[0].message.content)
        print("✅ Multi-model consensus reached: Metadata successfully audited and upgraded!")
        return final_intel
    except Exception as e:
        print(f"⚠️ Auditor model review skipped due to rate limit or error: {e}. Using creator draft.")
        return draft_intel

def run_pipeline(niche_topic: str):
    start_time = time.time()
    print("\n==================================================")
    print(f"🚀 LAUNCHING AUTONOMOUS POD PIPELINE: '{niche_topic}'")
    print("==================================================\n")
    
    try:
        # 1. AI Concept & Multi-Model Consensus Intelligence Generation
        intel = generate_listing_intelligence(niche_topic)
        
        print("\n--------------------------------------------------")
        print(f"💡 GROQ CONSENSUS INTELLIGENCE OUTPUT:")
        print(f"📌 Title: {intel.get('title')}")
        print(f"🎯 Target Audience: {intel.get('target_audience')}")
        print(f"🏷️ SEO Tags ({len(intel.get('tags', []))}): {', '.join(intel.get('tags', []))}")
        print(f"🎨 Recommended Colors: {intel.get('recommended_color_palette')}")
        print(f"💵 Suggested Retail: ${float(intel.get('suggested_retail_price', 25.00)):.2f}")
        print(f"🖼️ Engineered Image Prompt:\n   {intel.get('image_prompt')}")
        print("--------------------------------------------------\n")

        # 2. Artwork Generation & Processing
        filename = f"groq_{niche_topic.lower().replace(' ', '_')}.png"
        image_path = generate_artwork(intel["image_prompt"], filename)
        
        # 3. Printify Shop Connection
        shop_id = get_shop_id()
        print(f"🔑 Connected to Printify Shop ID: {shop_id}")
        
        # 4. Artwork Upload
        image_id = upload_artwork(image_path)
        
        # 5. Product Creation
        full_description = (
            f"{intel.get('description')}\n\n"
            f"• Target Fit: {intel.get('target_audience')}\n"
            f"• Style Keywords: {', '.join(intel.get('tags', []))}\n"
            f"• Care Instructions: Machine wash cold inside out with like colors."
        )
        
        product = create_tshirt_product(
            shop_id=shop_id,
            title=intel.get("title", f"Custom {niche_topic} Tee"),
            description=full_description,
            image_id=image_id
        )
        
        elapsed = time.time() - start_time
        print("\n==================================================")
        print("🎉 PIPELINE EXECUTION SUCCESSFUL!")
        print(f"⏱️ Total Execution Time: {elapsed:.2f} seconds")
        print(f"📦 Product Title: {product.get('title')}")
        print(f"🆔 Printify Product ID: {product.get('id')}")
        print("==================================================")

        # 6. Dispatch Success Email Report safely
        success_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #f9fff9;">
            <h2 style="color: #27ae60;">🎉 Autonomous POD Product Published!</h2>
            <p>Your autonomous agent discovered a live trend, designed artwork, optimized metadata, and published a new product draft on Printify.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <ul>
                <li><b>Discovered Trend Niche:</b> {niche_topic}</li>
                <li><b>Product Title:</b> {product.get('title')}</li>
                <li><b>Printify Product ID:</b> {product.get('id')}</li>
                <li><b>Total Execution Time:</b> {elapsed:.2f} seconds</li>
            </ul>
            <p style="color: #7f8c8d; font-size: 12px;">Autonomous Multi-Model AI Agent Report</p>
        </div>
        """
        safe_send_email(f"🚀 Autonomous POD Success: {intel.get('title')}", success_html)

    except Exception as e:
        elapsed = time.time() - start_time
        error_message = str(e)
        print(f"\n❌ Pipeline failed with error: {error_message}")
        
        # Dispatch Failure Email Report safely
        failure_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ffccd5; border-radius: 8px; background-color: #fff5f5;">
            <h2 style="color: #c0392b;">❌ Autonomous POD Pipeline Failed</h2>
            <p>The autonomous agent encountered an unhandled exception during execution.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <ul>
                <li><b>Niche Topic:</b> {niche_topic}</li>
                <li><b>Error Details:</b> <code style="color: #c0392b;">{error_message}</code></li>
                <li><b>Time Elapsed Before Failure:</b> {elapsed:.2f} seconds</li>
            </ul>
            <p style="color: #7f8c8d; font-size: 12px;">Autonomous Multi-Model AI Agent Error Report</p>
        </div>
        """
        safe_send_email(f"⚠️ Autonomous POD Pipeline Failure: {niche_topic}", failure_html)
        raise e

if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        print("🌐 No custom topic passed. Triggering Live Web Trend Discovery...")
        topic = fetch_trending_niches()
        
    run_pipeline(topic)
