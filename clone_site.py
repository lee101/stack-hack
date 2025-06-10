import asyncio
import json
import importlib
import subprocess
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import re


def sanitize_path(path: str) -> str:
    """Sanitize a URL path for saving as a local filename"""
    if path in ("", "/"):
        return "index.html"
    if path.endswith("/"):
        path += "index.html"
    elif "." not in Path(path).name:
        path += "/index.html"
    path = re.sub(r"[^a-zA-Z0-9_\-./]", "_", path)
    return path.lstrip("/")


async def fetch(session: ClientSession, url: str) -> str:
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""


def run_claude(prompt: str, system_message: str = None) -> str:
    """Invoke the local 'claude' CLI if available, otherwise fall back to API."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        try:
            module = importlib.import_module("claude_api")
            return module.query_to_claude_internal(
                prompt, system_message=system_message
            )
        except Exception as e:
            print(f"Claude invocation failed: {e}")
            return ""


def extract_dynamic_routes(html: str) -> set[str]:
    """Extract possible routes from JSON embedded in the page."""
    routes: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        text = script.string or ""
        if script.get("type", "").endswith("json"):
            text = text.strip()
        # quick regex to find path-like strings
        for match in re.findall(r"\"(/[^\"']+)\"", text):
            if match.startswith("/"):
                routes.add(match)
        try:
            data = json.loads(text)
        except Exception:
            continue
        if isinstance(data, dict):
            for key in ("routes", "pages", "paths"):
                val = data.get(key)
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, str) and item.startswith("/"):
                            routes.add(item)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and item.startswith("/"):
                    routes.add(item)
    return routes


def generate_route_code(
    domain: str,
    route: str,
    html: str,
    stack_desc: str | None = None,
    out_dir: str | Path = "generated_routes",
):
    """Generate code for a single route using Claude."""
    prompt = (
        f"Given the HTML for {route} on {domain}, "
        "produce the backend code needed to serve this route using the same technologies."
    )
    if stack_desc:
        prompt += f"\nStack details: {stack_desc}"
    try:
        result = run_claude(prompt, system_message="let's build the backend for this route")
        out = Path(out_dir)
        out.mkdir(exist_ok=True)
        fname = out / f"{sanitize_path(route)}.txt"
        fname.parent.mkdir(parents=True, exist_ok=True)
        fname.write_text(result, encoding="utf-8")
    except Exception as e:
        print(f"Error generating code for {route}: {e}")


async def clone_site(
    base_url: str,
    max_pages: int = 50,
    output_dir: str = "cloned",
    concurrency: int = 2,
    discover_sitemap: bool = False,
    generated_dir: str | Path = "generated_routes",
):
    """Recursively download pages starting from base_url."""
    visited: set[str] = set()
    queue: asyncio.Queue[str] = asyncio.Queue()
    await queue.put(base_url)
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    async with ClientSession() as session:
        if discover_sitemap:
            sitemap_url = urljoin(base_url, "/sitemap.xml")
            sitemap = await fetch(session, sitemap_url)
            if sitemap:
                for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap):
                    if loc.startswith(domain):
                        await queue.put(loc)

        async def worker():
            while len(visited) < max_pages:
                try:
                    url = await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    if queue.empty():
                        break
                    continue
                if url in visited:
                    queue.task_done()
                    continue
                html = await fetch(session, url)
                visited.add(url)
                queue.task_done()
                if not html:
                    continue
                rel_path = sanitize_path(url.replace(domain, ""))
                file_path = out_path / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(html, encoding="utf-8")

                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = urljoin(url, a["href"])
                    if href.startswith(domain) and href not in visited:
                        await queue.put(href)

                for r in extract_dynamic_routes(html):
                    href = urljoin(domain, r)
                    if href.startswith(domain) and href not in visited:
                        await queue.put(href)

                generate_route_code(domain, url, html, out_dir=generated_dir)

        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)

    (Path(output_dir) / "visited.json").write_text(json.dumps(sorted(visited)), encoding="utf-8")
    return visited


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recursively clone a site")
    parser.add_argument("url", help="Base URL to clone, e.g. https://example.com")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to fetch")
    parser.add_argument("--output", default="cloned", help="Directory to store pages")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent workers")
    parser.add_argument("--discover-sitemap", action="store_true", help="Try to fetch sitemap.xml for extra routes")
    args = parser.parse_args()

    asyncio.run(
        clone_site(
            args.url,
            max_pages=args.max_pages,
            output_dir=args.output,
            concurrency=args.concurrency,
            discover_sitemap=args.discover_sitemap,
        )
    )
