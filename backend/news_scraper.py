import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import os
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BangladeshNewsScraper:
    def __init__(self):
        self.dhaka_locations = {
            'Mirpur': {'name': 'Mirpur, Dhaka', 'coordinates': [23.8067, 90.3686]},
            'Motijheel': {'name': 'Motijheel, Dhaka', 'coordinates': [23.7361, 90.4196]},
            'Shahbagh': {'name': 'Shahbagh, Dhaka', 'coordinates': [23.7361, 90.3935]},
            'Gulshan': {'name': 'Gulshan, Dhaka', 'coordinates': [23.7803, 90.4194]},
            'Dhanmondi': {'name': 'Dhanmondi, Dhaka', 'coordinates': [23.7461, 90.3742]},
            'Uttara': {'name': 'Uttara, Dhaka', 'coordinates': [23.8759, 90.3795]},
            'Wari': {'name': 'Wari, Dhaka', 'coordinates': [23.7197, 90.4264]},
            'Ramna': {'name': 'Ramna, Dhaka', 'coordinates': [23.7350, 90.3833]},
            'Tejgaon': {'name': 'Tejgaon, Dhaka', 'coordinates': [23.7574, 90.3957]},
            'Badda': {'name': 'Badda, Dhaka', 'coordinates': [23.7783, 90.4267]}
        }
        
        self.parties = [
            'Awami League', 'Bangladesh Nationalist Party', 'BNP', 'Jubo League',
            'Jatiya Party', 'Jamaat-e-Islami', 'Communist Party', 'Workers Party',
            'Gono Forum', 'Bikalpa Dhara', 'Liberal Democratic Party'
        ]

    async def extract_location(self, text):
        for location, data in self.dhaka_locations.items():
            if location.lower() in text.lower():
                return data['name'], data['coordinates']
        
        if 'dhaka' in text.lower():
            return "Dhaka, Bangladesh", [23.8103, 90.4125]
        
        return "Bangladesh", [23.6850, 90.3563]

    async def extract_party(self, text):
        text_lower = text.lower()
        for party in self.parties:
            if party.lower() in text_lower:
                return party
        return "Unknown"

    async def extract_casualties(self, text):
        deaths = 0
        injured = 0
        
        death_patterns = [
            r'(\d+)\s*(?:dead|killed|death|fatalities|died|loses life)',
            r'(\d+)\s*(?:people|persons|individuals)\s*(?:dead|killed|died)',
            r'death\s*(?:toll|count)?\s*(?:of|:)?\s*(\d+)'
        ]
        
        injury_patterns = [
            r'(\d+)\s*(?:injured|hurt|wounded|hospitalized)',
            r'(\d+)\s*(?:people|persons|individuals)\s*(?:injured|hurt|wounded)',
            r'injur(?:y|ies)\s*(?:count|toll)?\s*(?:of|:)?\s*(\d+)'
        ]
        
        for pattern in death_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                deaths = max(deaths, int(match.group(1)))
        
        for pattern in injury_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                injured = max(injured, int(match.group(1)))
        
        return deaths, injured

    async def fetch_article_content(self, page, url, max_retries=2):
        for attempt in range(1, max_retries + 1):
            try:
                await page.goto(url, timeout=30000, wait_until='load')
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()

                article_selectors = [
                    'article', '.article-content', '.story-content', 
                    '.news-content', '.post-content', '.content',
                    'div[class*="content"]', 'div[class*="article"]'
                ]

                text = ""
                for selector in article_selectors:
                    article_elem = soup.select_one(selector)
                    if article_elem:
                        text = article_elem.get_text(strip=True)
                        break

                if not text:
                    text = soup.get_text(strip=True)

                return text[:10000]

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {url}: {e}")
                if attempt == max_retries:
                    logger.error(f"Giving up on {url} after {max_retries} attempts.")
                    return ""
                await asyncio.sleep(2)

    async def crawl_news_site(self, site_config, max_articles=50):
        articles = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                bypass_csp=True,
                java_script_enabled=True,
            )

            async def route_intercept(route):
                if route.request.resource_type in ["image", "font"]:
                    await route.abort()
                else:
                    await route.continue_()

            await context.route("**/*", route_intercept)
            page = await context.new_page()

            try:
                logger.info(f"Crawling {site_config['name']}...")
                await page.goto(site_config['url'], timeout=120000, wait_until='load')
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                article_links = []
                for selector in site_config['selectors']:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(site_config['url'], href)
                            title = link.get_text(strip=True)
                            if title and len(title) > 10:
                                article_links.append({'url': full_url, 'title': title})

                seen_urls = set()
                unique_links = []
                for link in article_links:
                    if link['url'] not in seen_urls:
                        seen_urls.add(link['url'])
                        unique_links.append(link)

                for i, link in enumerate(unique_links[:max_articles]):
                    try:
                        logger.info(f"Fetching article {i+1}/{len(unique_links)}: {link['title'][:50]}...")
                        article_text = await self.fetch_article_content(page, link['url'])

                        if article_text:
                            location, coordinates = await self.extract_location(article_text)
                            party = await self.extract_party(article_text)
                            deaths, injured = await self.extract_casualties(article_text)

                            articles.append({
                                'title': link['title'],
                                'link': link['url'],
                                'date': datetime.now().isoformat(),
                                'source': site_config['name'],
                                'location': location,
                                'party': party,
                                'deaths': deaths,
                                'injured': injured,
                                'coordinates': coordinates,
                                'content_preview': article_text[:1000]
                            })

                    except Exception as e:
                        logger.error(f"Error processing article {link['url']}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error crawling {site_config['name']}: {e}")

            finally:
                await browser.close()

        return articles

    async def crawl_all_sites(self):
        sites = [
            {
                'name': 'Prothom Alo',
                'url': 'https://www.prothomalo.com',
                'selectors': [
                    'a[href*="/politics/"]',
                    'a[href*="/bangladesh/"]',
                    '.story-card a',
                    '.headline a'
                ]
            },
            {
                'name': 'The Daily Star',
                'url': 'https://www.thedailystar.net',
                'selectors': [
                    'a[href*="/politics"]',
                    'a[href*="/bangladesh"]',
                    '.story-title a',
                    '.news-title a'
                ]
            },
            {
                'name': 'Dhaka Tribune',
                'url': 'https://www.dhakatribune.com',
                'selectors': [
                    'a[href*="/politics"]',
                    'a[href*="/bangladesh"]',
                    '.story-headline a',
                    '.post-title a'
                ]
            },
            {
                'name': 'New Age',
                'url': 'https://www.newagebd.net',
                'selectors': [
                    'a[href*="/politics"]',
                    'a[href*="/bangladesh"]',
                    '.news-title a'
                ]
            }
        ]

        all_articles = []
        
        async def process_site(site):
            try:
                articles = await self.crawl_news_site(site)
                return articles
            except Exception as e:
                logger.error(f"Failed to scrape {site['name']}: {e}")
                return []

        tasks = [process_site(site) for site in sites]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for site, result in zip(sites, results):
            if isinstance(result, list):
                all_articles.extend(result)
                logger.info(f"Scraped {len(result)} articles from {site['name']}")
            else:
                logger.error(f"Error processing {site['name']}: {result}")

        return all_articles

    async def save_data(self, articles, filename='news_data.json'):
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} articles to {filepath}")

async def main():
    scraper = BangladeshNewsScraper()
    try:
        articles = await scraper.crawl_all_sites()
        await scraper.save_data(articles)
        print(f"\nScraping completed!")
        print(f"Total articles scraped: {len(articles)}")
        sources = {}
        for article in articles:
            source = article['source']
            sources[source] = sources.get(source, 0) + 1
        print("\nArticles by source:")
        for source, count in sources.items():
            print(f"  {source}: {count} articles")
    except Exception as e:
        logger.error(f"Main execution failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())


