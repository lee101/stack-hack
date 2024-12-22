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

