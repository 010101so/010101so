# Bot Scanner

import asyncio
import requests

async def fetch(url):
    response = requests.get(url)
    return response.json()

async def main():
    urls = ['http://example.com/api1', 'http://example.com/api2']
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())