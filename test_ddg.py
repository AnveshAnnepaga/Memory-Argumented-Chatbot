import asyncio, httpx
from bs4 import BeautifulSoup

async def test():
    resp = await httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}).post(
        'https://lite.duckduckgo.com/lite/', data={'q': 'vikram rocket startup'}
    )
    soup = BeautifulSoup(resp.text, 'html.parser')
    for r in soup.select('tr')[:6]:
        print('--- ROW ---')
        title = r.select_one('.result-title')
        snippet = r.select_one('.result-snippet')
        if title: print('TITLE:', title.get_text(strip=True))
        if snippet: print('SNIPPET:', snippet.get_text(strip=True))

asyncio.run(test())
