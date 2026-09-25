import os
import json
from dotenv import load_dotenv
from groq import Groq

# Flexible import handling for ddgs and duckduckgo_search
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY is missing from your .env file.")

client = Groq(api_key=GROQ_API_KEY)

def fetch_trending_niches() -> str:
    """
    Scans live web searches using DDGS to discover current 
    viral internet subcultures, gaming trends, and apparel aesthetics.
    """
    print("🌐 [Trend Discovery] Scanning live web search queries for viral aesthetics & subcultures...")
    
    # Target search queries for visual trends and subcultures
    search_queries = [
        "trending aesthetic subcultures 2026",
        "viral streetwear clothing trends 2026",
        "popular graphic tee aesthetics"
    ]
    
    scraped_snippets = []
    
    try:
        with DDGS() as ddgs:
            for query in search_queries:
                print(f"🔍 Searching DuckDuckGo for: '{query}'...")
                try:
                    # Retrieve web search results cleanly
                    results = list(ddgs.text(query, max_results=4))
                    for r in results:
                        title = r.get("title", "")
                        body = r.get("body", "")
                        if title or body:
                            scraped_snippets.append(f"Title: {title}\nSnippet: {body}\n")
                except Exception as e:
                    print(f"⚠️ Warning: Search query failed for '{query}': {e}")
    except Exception as e:
        print(f"⚠️ Error initializing DDGS search client: {e}")
                
    combined_context = "\n---\n".join(scraped_snippets)
    
    if not combined_context.strip():
        print("⚠️ Warning: Live web search returned empty. Falling back to default high-converting evergreen niche.")
        return "Cyberpunk Retro Samurai"

    print("🧠 [Trend Intelligence] Analyzing scraped web data to select the most profitable t-shirt niche...")
    
    prompt = f"""
    You are an expert e-commerce trend analyst and Print-on-Demand product strategist.
    Review the following live web search snippets regarding current internet culture, aesthetics, and trends:
    
    {combined_context}
    
    Your task: Extract or synthesize ONE highly specific, visually compelling, and profitable t-shirt niche topic that people would eagerly buy on a graphic tee. 
    Examples of good outputs: "Synthwave Cyber Cat", "Neon Cyberpunk Samurai", "Minimalist Tarot Mysticism", "Retro Glitch Gamer".
    
    You MUST output valid JSON format with a single key named "selected_niche" containing a short phrase (2 to 4 words max).
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        data = json.loads(response.choices[0].message.content)
        niche = data.get("selected_niche", "Cyberpunk Retro Samurai")
        print(f"🎯 Successfully Discovered Live Trend Niche: '{niche}'")
        return niche
    except Exception as e:
        print(f"⚠️ Error parsing trend selection: {e}. Using fallback niche.")
        return "Cyberpunk Retro Samurai"

if __name__ == "__main__":
    print("🧪 Testing Live Trend Discovery Module...")
    niche_result = fetch_trending_niches()
    print(f"\n==========================================")
    print(f"🔥 FINAL TREND DISCOVERY OUTPUT: {niche_result}")
    print(f"==========================================")
