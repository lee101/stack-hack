import os
from pathlib import Path
import random
import re
from typing import Optional

from bs4 import BeautifulSoup, Comment
from filecache import file_cache
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def gemini_generation(input_text: str, history: Optional[list] = None, system_instruction: Optional[str] = None) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    if key != api_key:
        genai.configure(api_key=key)

    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        # model_name="gemini-2.0-flash-exp",
        model_name="gemini-1.5-flash-8b",
        generation_config=generation_config,
        system_instruction=system_instruction
    )

    chat_session = model.start_chat(
        history=history if history else []
    )

    response = chat_session.send_message(input_text)
    return response.text


results_dir = Path(os.getenv("RESULTS_DIR", "results"))
prompt_results_dir = Path(os.getenv("PROMPT_RESULTS_DIR", "prompt_results"))

def clean_html_for_prompt(html_content: str) -> str:
    """Remove noisy tags and large base64 blobs from HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    # Strip HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove tags that rarely contain useful text
    for tag in soup([
        "script",
        "style",
        "canvas",
        "video",
        "audio",
        "svg",
        "meta",
        "link",
        "nav",
        "footer",
        "header",
    ]):
        tag.decompose()
    cleaned = str(soup)
    # remove data URIs
    cleaned = re.sub(r'data:image/[^;]+;base64,[^"\'\s>]+', '', cleaned)
    # remove long base64-like strings
    cleaned = re.sub(r'[A-Za-z0-9+/]{1000,}={0,2}', '', cleaned)
    # collapse repeated whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()
def analyze_html_content(html_content: str) -> str:
    """Analyzes HTML content using Gemini to determine tech stack"""
    cleaned = clean_html_for_prompt(html_content)
    prompt = (
        f"{cleaned}\n\n\nPlease give a detailed breakdown of the stack used to"
        " make this site, cdn, js libraries css libraries, techniques etc used to"
        " make this site :)"
    )

    # Get analysis from Gemini
    return gemini_generation(prompt)

@file_cache(cache_dir="cache")
def get_similar_domain_names(domain: str) -> list[str]:
    """Get similar domain names using Gemini"""
    # First get initial similar sites
    # prompt = f"What are 5 similar domains to midjourney.com? Only list real domain names, one per line."
    history = []
    
#     history.append({"role": "user", "parts": [prompt]})
#     history.append({"role": "model", "parts": ["""craiyon.com
# krea.ai 
# artbreeder.com
# imagine.com
# runwayml.com"""]})
    prompt = f"What are 5 similar domains to {domain}? Only list real domain names, one per line."

    domain_example = random.choice([
        "craiyon.com",
        "krea.ai",
        "artbreeder.com",
        "imagine.com",
        "runwayml.com",
        "photopea.com",
        "looka.com",
        "canva.com",
        "designevo.com",
        "fotor.com",
        "pixlr.com",
        "picmonkey.com",
        "crello.com",
        "midjourney.com",
        "clipdrop.co",
        "nike.com",
        "amazon.com",
        "google.com",
        "facebook.com",
        "twitter.com",
        "instagram.com",
        "youtube.com",
        "linkedin.com",
        "pinterest.com",
    ])
    
    more_sites = gemini_generation(prompt, history, system_instruction=f"You are a helpful assistant that provides domain names of other popular sites given a domain, different varieties. Only provide real domain names, one per line. eg: {domain_example}").strip().split('\n')
    
    return more_sites

def analyze_site(domain: str) -> str:
    # Check if results directory exists
    if not results_dir.exists():
        print("Results directory not found")
        results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create prompt results directory if it doesn't exist
    if not prompt_results_dir.exists():
        prompt_results_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = results_dir / f"{domain}.html"
    analysis_file = prompt_results_dir / f"{domain}_analysis.txt"
    
    # Always check cached analysis file
    if analysis_file.exists():
        try:
            cached_analysis = analysis_file.read_text(encoding='utf-8')
            return cached_analysis
        except Exception as e:
            print(f"Error reading cached analysis for {domain}: {str(e)}")
    
    try:
        # Read HTML content
        html_content = file_path.read_text(encoding="utf-8")

        # Get analysis from Gemini
        analysis = analyze_html_content(html_content)

        # Save analysis to a new file in prompt_results directory
        analysis_file.write_text(
            f"Analysis for {domain}:\n\n{analysis}", encoding="utf-8"
        )

        print(f"Completed analysis for {domain}")
        return analysis

    except Exception as e:
        print(f"Error analyzing {domain}: {str(e)}")
        return ""