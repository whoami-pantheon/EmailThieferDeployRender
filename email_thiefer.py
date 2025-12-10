import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

async def run_email_thiefer(start_url: str) -> list[str]:
    """
    Crawls a given URL and its internal links to extract email addresses.
    Returns a sorted list of unique email addresses found.
    """
    internal_urls = set()
    found_emails = set()
    domain_name = urlparse(start_url).netloc

    def is_valid_url(url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    async def get_emails_and_links_from_url(session, url):
        nonlocal found_emails, internal_urls
        urls_on_page = set()
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            async with session.get(url, ssl=False, headers=headers, timeout=10) as response: # Added timeout
                if response.status != 200:
                    return urls_on_page
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

                # Extract emails
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
                found_emails.update(emails)

        except Exception:
            # print(f"Error fetching {url}: {e}") # Removed print for web app
            return urls_on_page

        for a_tag in soup.find_all("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                continue
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not is_valid_url(href):
                continue
            if href in internal_urls:
                continue
            if not parsed_href.netloc.endswith(domain_name):
                continue
            urls_on_page.add(href)
            internal_urls.add(href)
        return urls_on_page

    urls_to_visit = {start_url}
    crawled_urls = set()

    async with aiohttp.ClientSession() as session:
        while urls_to_visit:
            crawl_batch = set()
            while urls_to_visit:
                url_to_add = urls_to_visit.pop()
                if url_to_add not in crawled_urls:
                    crawl_batch.add(url_to_add)

            if not crawl_batch:
                break

            tasks = {asyncio.create_task(get_emails_and_links_from_url(session, u)) for u in crawl_batch}
            crawled_urls.update(crawl_batch)

            done, pending = await asyncio.wait(tasks)

            for task in done:
                new_links = task.result()
                for link in new_links:
                    if link not in crawled_urls and link not in urls_to_visit:
                        urls_to_visit.add(link)
    
    return sorted(list(found_emails))
