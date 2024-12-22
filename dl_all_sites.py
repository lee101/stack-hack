import os
import csv
import asyncio
import aiohttp
import ssl
from typing import List
from pathlib import Path

# Create results directory if it doesn't exist
results_dir = Path('results')
results_dir.mkdir(exist_ok=True)

async def download_site(session: aiohttp.ClientSession, domain: str):
    # Check if file already exists before downloading
    filename = results_dir / f'{domain}.html'
    if filename.exists():
        print(f'File already exists for {domain}, skipping')
        return
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
        
    try:
        # Add random delay between requests
        # await asyncio.sleep(1 + (0.5 * random.random()))
        
        async with session.get(f'https://{domain}', 
                             headers=headers,
                             timeout=aiohttp.ClientTimeout(total=20),
                             max_redirects=5,
                             allow_redirects=True,
                             verify_ssl=False) as response:
            
            if response.status == 403:
                # Try with different User-Agent if blocked
                headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
                async with session.get(f'https://{domain}', headers=headers) as mobile_response:
                    content = await mobile_response.text()
            else:
                content = await response.text()
            
            # Save to file named after domain
            filename.write_text(content, encoding='utf-8')
                
            print(f'Successfully downloaded {domain}')
            
    except ssl.SSLCertVerificationError:
        try:
            # Retry with http if https certificate fails
            async with session.get(f'http://{domain}', headers=headers, timeout=aiohttp.ClientTimeout(total=20), max_redirects=5) as response:
                content = await response.text()
                
                filename.write_text(content, encoding='utf-8')
                    
                print(f'Successfully downloaded {domain} using http')
                
        except Exception as e:
            print(f'Error downloading {domain} with http: {str(e)}')
            
    except Exception as e:
        print(f'Error downloading {domain}: {str(e)}')
async def download_all_sites(domains: List[str]):
    async with aiohttp.ClientSession() as session:
        # Process in chunks of 30 domains
        for i in range(0, len(domains), 30):
            chunk = domains[i:i+30]
            tasks = []
            for domain in chunk:
                task = asyncio.ensure_future(download_site(session, domain.strip()))
                tasks.append(task)
            await asyncio.gather(*tasks)
            print(f"Completed chunk {i//30 + 1}")

async def download_single_site(domain: str) -> str:
    """Downloads a single site asynchronously and returns the HTML content"""
    async with aiohttp.ClientSession() as session:
        filename = results_dir / f'{domain}.html'
        if filename.exists():
            print(f'File already exists for {domain}, skipping')
            return filename.read_text(encoding='utf-8')
            
        try:
            async with session.get(f'https://{domain}', timeout=aiohttp.ClientTimeout(total=20), max_redirects=5) as response:
                content = await response.text()
                
                # Save to file named after domain
                filename.write_text(content, encoding='utf-8')
                    
                print(f'Successfully downloaded {domain}')
                return content
                
        except ssl.SSLCertVerificationError:
            try:
                # Retry with http if https certificate fails
                async with session.get(f'http://{domain}', timeout=aiohttp.ClientTimeout(total=20), max_redirects=5) as response:
                    content = await response.text()
                    
                    filename.write_text(content, encoding='utf-8')
                        
                    print(f'Successfully downloaded {domain} using http')
                    return content
                    
            except Exception as e:
                print(f'Error downloading {domain} with http: {str(e)}')
                return ""
                
        except Exception as e:
            print(f'Error downloading {domain}: {str(e)}')
            return ""

if __name__ == "__main__":
    # Read domains from CSV file
    domains = []
    csv_file = Path('cloudflare-radar_top-1000000-domains_20241213-20241220.csv')
    with csv_file.open('r') as f:
        reader = csv.reader(f)
        domains = [row[0] for row in reader]

    # Run async downloads with semaphore to limit concurrent requests
    asyncio.run(download_all_sites(domains))
