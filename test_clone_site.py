import asyncio
from aiohttp import web
from pathlib import Path
import pytest
from clone_site import clone_site
from urllib.parse import urlparse


async def create_test_server():
    async def index(request):
        return web.Response(
            text='''<a href="/about">About</a><script type="application/json">{"routes": ["/api"]}</script>'''
        )

    async def about(request):
        return web.Response(text='<a href="/">Home</a>')

    async def api(request):
        return web.Response(text='ok')

    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/about', about)
    app.router.add_get('/api', api)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, f'http://localhost:{port}'


@pytest.mark.asyncio
async def test_clone_site(tmp_path, monkeypatch):
    runner, base_url = await create_test_server()
    import types, sys
    sys.modules['claude_api'] = types.SimpleNamespace(
        query_to_claude_internal=lambda *a, **k: "code"
    )

    gen_dir = tmp_path / 'gen'
    visited = await clone_site(
        base_url,
        max_pages=5,
        output_dir=tmp_path,
        generated_dir=gen_dir,
    )
    assert '/api' in {urlparse(u).path for u in visited}
    assert (tmp_path / 'index.html').exists()
    assert (tmp_path / 'about' / 'index.html').exists()
    assert (tmp_path / 'api' / 'index.html').exists()
    assert (gen_dir / 'api.txt').exists() or (gen_dir / 'api' / 'index.html.txt').exists()
    assert (tmp_path / 'visited.json').exists()
    await runner.cleanup()
