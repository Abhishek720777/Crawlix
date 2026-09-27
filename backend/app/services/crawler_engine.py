import re
import json
import time
import random
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from textblob import TextBlob

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

class CrawlerEngine:
    """Production-grade Web Scraper Engine with intelligent extractors"""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        start_time = time.time()
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                elapsed_ms = (time.time() - start_time) * 1000.0
                return {
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "html": response.text,
                    "response_time_ms": round(elapsed_ms, 2),
                    "error": None
                }
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return {
                "url": url,
                "status_code": 0,
                "html": "",
                "response_time_ms": round(elapsed_ms, 2),
                "error": str(e)
            }

    def parse_page(self, url: str, html: str, crawler_type: str = "generic", custom_selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if not html:
            return {"title": "No HTML Content", "data": {}, "discovered_links": []}

        soup = BeautifulSoup(html, "lxml" if "lxml" in BeautifulSoup.NO_PARSERS else "html.parser")
        
        # 1. Base Meta Extraction
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        meta_desc = ""
        meta_desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_desc_tag and meta_desc_tag.get("content"):
            meta_desc = meta_desc_tag.get("content").strip()

        og_image = ""
        og_image_tag = soup.find("meta", attrs={"property": "og:image"})
        if og_image_tag and og_image_tag.get("content"):
            og_image = og_image_tag.get("content").strip()

        # 2. Extract Discovered Links (internal/external)
        base_domain = urlparse(url).netloc
        discovered_links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            full_url = urljoin(url, href)
            if urlparse(full_url).scheme in ("http", "https"):
                discovered_links.append(full_url)
        discovered_links = list(set(discovered_links))[:30]  # capped for queue efficiency

        # 3. Handle Custom CSS Selectors
        extracted_data: Dict[str, Any] = {
            "meta_description": meta_desc,
            "og_image": og_image,
        }

        if custom_selectors:
            for field, selector in custom_selectors.items():
                elements = soup.select(selector)
                if len(elements) == 1:
                    extracted_data[field] = elements[0].get_text(strip=True)
                elif len(elements) > 1:
                    extracted_data[field] = [el.get_text(strip=True) for el in elements[:20]]
                else:
                    extracted_data[field] = None

        # 4. Built-in Preset Extractors
        if crawler_type == "ecommerce":
            extracted_data.update(self._extract_ecommerce_intelligence(soup))
        elif crawler_type == "news":
            extracted_data.update(self._extract_news_intelligence(soup))
        elif crawler_type == "schema":
            extracted_data.update(self._extract_json_ld(soup))
        else:
            extracted_data.update(self._extract_generic_intelligence(soup))

        return {
            "title": title,
            "data": extracted_data,
            "discovered_links": discovered_links
        }

    def _extract_ecommerce_intelligence(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract pricing, discount, currency, availability, and rating signals"""
        text = soup.get_text()
        
        # Regex for price detection: $19.99, €25,00, £45.50, ₹1,299
        prices = re.findall(r"[\$\€\£\₹]\s?(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)", text)
        clean_prices = []
        for p in prices:
            try:
                num = float(p.replace(",", ""))
                if 0.1 <= num <= 100000.0:
                    clean_prices.append(num)
            except ValueError:
                continue

        detected_price = clean_prices[0] if clean_prices else None
        avg_price = round(sum(clean_prices) / len(clean_prices), 2) if clean_prices else None

        # In-stock detection
        text_lower = text.lower()
        in_stock = True
        if "out of stock" in text_lower or "currently unavailable" in text_lower or "sold out" in text_lower:
            in_stock = False

        # Brand or SKU
        sku = None
        sku_tag = soup.find(attrs={"itemprop": "sku"}) or soup.find(attrs={"data-sku": True})
        if sku_tag:
            sku = sku_tag.get_text(strip=True) or sku_tag.get("data-sku")

        return {
            "detected_price": detected_price,
            "all_price_occurrences": clean_prices[:10],
            "average_price_on_page": avg_price,
            "in_stock": in_stock,
            "sku": sku,
            "product_keywords": self._extract_key_phrases(text, max_phrases=5)
        }

    def _extract_news_intelligence(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract headline, article paragraphs, sentiment polarity & key entities"""
        # Collect paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
        full_article_text = " ".join(paragraphs[:15])

        sentiment_score = 0.0
        sentiment_label = "neutral"
        if full_article_text:
            try:
                blob = TextBlob(full_article_text)
                sentiment_score = round(blob.sentiment.polarity, 3)
                if sentiment_score > 0.1:
                    sentiment_label = "positive"
                elif sentiment_score < -0.1:
                    sentiment_label = "negative"
            except Exception:
                pass

        # Author / Published Date
        author = None
        author_tag = soup.find(attrs={"name": "author"}) or soup.find(attrs={"rel": "author"})
        if author_tag:
            author = author_tag.get("content") or author_tag.get_text(strip=True)

        return {
            "word_count": len(full_article_text.split()),
            "paragraphs_count": len(paragraphs),
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "author": author,
            "key_entities": self._extract_key_phrases(full_article_text, max_phrases=8),
            "article_summary": full_article_text[:350] + "..." if len(full_article_text) > 350 else full_article_text
        }

    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured Schema.org JSON-LD definitions"""
        schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                schemas.append(data)
            except Exception:
                continue
        return {"json_ld_schemas": schemas}

    def _extract_generic_intelligence(self, soup: BeautifulSoup) -> Dict[str, Any]:
        headings_h1 = [h.get_text(strip=True) for h in soup.find_all("h1")][:5]
        headings_h2 = [h.get_text(strip=True) for h in soup.find_all("h2")][:8]
        images = [img.get("src") for img in soup.find_all("img", src=True)][:10]
        
        # Word density
        text = soup.get_text(separator=" ", strip=True)
        return {
            "h1_tags": headings_h1,
            "h2_tags": headings_h2,
            "sample_images": images,
            "key_phrases": self._extract_key_phrases(text, max_phrases=6)
        }

    def _extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        words = re.findall(r"\b[A-Za-z]{4,20}\b", text)
        stopwords = {"about", "there", "their", "which", "would", "these", "other", "could", "first", "after"}
        frequency: Dict[str, int] = {}
        for w in words:
            wl = w.lower()
            if wl not in stopwords and not wl.isdigit():
                frequency[wl] = frequency.get(wl, 0) + 1
        sorted_phrases = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        return [f"{phrase} ({count})" for phrase, count in sorted_phrases[:max_phrases]]

crawler_engine = CrawlerEngine()
