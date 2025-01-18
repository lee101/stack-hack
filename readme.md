# StackHack.netwrck.com

A powerful tool for analyzing tech stacks of any website. Simply enter a domain and get free detailed insights about:

- Frontend frameworks and libraries
- Backend technologies 
- CDNs in use
- JavaScript libraries
- CSS frameworks
- Build tools and techniques

## Features

- Fast analysis powered by Gemini AI
- Similar domain suggestions
- Clean FastAPI backend
- Jinja2 templating
- Efficient caching
- XML sitemaps for SEO

## Routes

- `/` - Home page with example domains
- `/stack/{domain}` - Get detailed stack analysis for any domain
- `/sitemap{1-34}.xml` - XML sitemaps for search engines

## Setup

Quick setup using `uv` for Python dependency management:

uv pip compile requirements.in -o requirements.txt && uv pip install -r requirements.txt  --python .venv/bin/python

./.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -b :7345 main:app --timeout 6000 --workers 1