import csv
from pathlib import Path
from fastapi import FastAPI, HTTPException
from prompt_gemini import analyze_site, get_similar_domain_names

app = FastAPI()
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    domains = [
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
        "crello.com"
    ]
    #todo solve midjourney.com cloudflare blocking
    return templates.TemplateResponse("index.jinja2", {"request": request, "domains": domains})

@app.get("/stack/{domain}")
async def get_stack_analysis(request: Request, domain: str):
    try:
        # Download site first
        from dl_all_sites import download_single_site
        html_content = await download_single_site(domain)
        domains = get_similar_domain_names(domain)
        
        # Then analyze it
        analysis = analyze_site(domain)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis not found for domain: {domain}")
        return templates.TemplateResponse("stack.jinja2", {
            "request": request,
            "domain": domain,
            "analysis": analysis,
            "domains": domains
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Global file data
csv_file = Path('cloudflare-radar_top-1000000-domains_20241213-20241220.csv')

# Read all domains into memory globally
all_domains = []
with csv_file.open('r') as f:
    reader = csv.reader(f)
    all_domains = [row[0] for row in reader]

@app.get("/sitemap{num}.xml") 
async def get_sitemap(num: int):
    if num < 1 or num > 34:
        raise HTTPException(status_code=404, detail="Invalid sitemap number")
        
    # Get slice of domains for this sitemap (30k domains per sitemap)
    start = (num-1) * 30000
    end = num * 30000
    domains = all_domains[start:end]

    # Generate sitemap XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for domain in domains:
        xml += f'  <url>\n'
        xml += f'    <loc>https://yourdomain.com/stack/{domain}</loc>\n'
        xml += f'    <changefreq>weekly</changefreq>\n'
        xml += f'  </url>\n'
    
    xml += '</urlset>'

    from fastapi.responses import Response
    return Response(content=xml, media_type="application/xml")


