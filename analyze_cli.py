import argparse
from prompt_gemini import analyze_site

parser = argparse.ArgumentParser(description="Analyze tech stack of a domain")
parser.add_argument("domain", help="Domain to analyze")
args = parser.parse_args()

print(analyze_site(args.domain))
