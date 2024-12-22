import os
import google.generativeai as genai
from typing import Optional
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def gemini_generation(input_text: str, history: Optional[list] = None) -> str:

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
    )

    chat_session = model.start_chat(
        history=history if history else []
    )

    response = chat_session.send_message(input_text)
    return response.text

def analyze_all_sites():
    results_dir = 'results'
    prompt_results_dir = 'prompt_results'
    def analyze_site(domain: str, results_dir: str = 'results', prompt_results_dir: str = 'prompt_results') -> str:
        # Check if results directory exists
        if not os.path.exists(results_dir):
            print("Results directory not found")
            return ""
        
        # Create prompt results directory if it doesn't exist
        if not os.path.exists(prompt_results_dir):
            os.makedirs(prompt_results_dir)
        
        file_path = os.path.join(results_dir, domain)
        analysis_file = os.path.join(prompt_results_dir, f"{domain}_analysis.txt")
        
        # Always check cached analysis file
        if os.path.exists(analysis_file):
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    cached_analysis = f.read()
                return cached_analysis
            except Exception as e:
                print(f"Error reading cached analysis for {domain}: {str(e)}")
        
        try:
            # Read HTML content
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create prompt with HTML content
            prompt = f"{html_content}\n\n\nPlease give a detailed breakdown of the stack used to make this site, cdn, js libraries css libraries, techniques etc used to make this site :)"
            
            # Get analysis from Gemini
            analysis = gemini_generation(prompt)
            
            # Save analysis to a new file in prompt_results directory
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(f"Analysis for {domain}:\n\n{analysis}")
                
            print(f"Completed analysis for {domain}")
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {domain}: {str(e)}")
            return ""

if __name__ == "__main__":
    analyze_all_sites()