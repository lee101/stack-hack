import pytest
from dl_all_sites import download_single_site
from pathlib import Path

@pytest.mark.asyncio
async def test_download_midjourney():
    # Test downloading midjourney.com
    domain = "midjourney.com"
    
    # Delete existing file if it exists
    results_dir = Path('results')
    test_file = results_dir / f'{domain}.html'
    if test_file.exists():
        test_file.unlink()
    
    # Download the site
    content = await download_single_site(domain)
    
    # Verify content was downloaded
    assert content != ""
    assert test_file.exists()
    
    # Verify file contains actual HTML content
    file_content = test_file.read_text(encoding='utf-8')
    assert "<!DOCTYPE html>" in file_content.lower() or "<html" in file_content.lower()
