import re
import json
import time
import random
import socket
import ipaddress
from typing import Dict, Any, List, Optional, Tuple
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

MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB limit to prevent compression bombs / OOM


def is_safe_public_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validates URL to protect against SSRF.
    Rejects non-HTTP(S) protocols and private, loopback, link-local, or reserved IPs.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Unsupported scheme: {parsed.scheme}"

        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL hostname"

        # Block well-known internal hostnames
        if hostname.lower() in ("localhost", "postgres", "redis", "api", "worker_1", "worker_2", "celery_beat", "host.docker.internal"):
            return False, f"Access to internal host '{hostname}' is forbidden."

        # Resolve IP addresses for hostname
        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            return False, f"DNS resolution failed: {e}"

        for entry in addr_info:
            ip_str = entry[4][0]
            ip = ipaddress.ip_address(ip_str)

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False, f"Access to non-public IP ({ip_str}) is forbidden."

        return True, None
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


class CrawlerEngine:
    """Production-grade Web Scraper Engine with SSRF mitigation and streaming limits."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        # SSRF Pre-flight check
        safe, reason = is_safe_public_url(url)
        if not safe:
            return {
                "url": url,
                "status_code": 403,
                "html": "",
                "response_time_ms": 0.0,
                "error": f"SSRF Blocked: {reason}"
            }

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
                async with client.stream("GET", url, headers=headers) as response:
                    # Validate redirected URL as well
                    final_safe, final_reason = is_safe_public_url(str(response.url))
                    if not final_safe:
                        return {
                            "url": str(response.url),
                            "status_code": 403,
                            "html": "",
                            "response_time_ms": round((time.time() - start_time) * 1000.0, 2),
                            "error": f"SSRF Redirect Blocked: {final_reason}"
                        }

                    # Check Content-Type (skip huge binaries like ISOs or zips)
                    content_type = response.headers.get("content-type", "").lower()
                    if content_type and not any(t in content_type for t in ("text/", "html", "xml", "json")):
                        return {
                            "url": str(response.url),
                            "status_code": response.status_code,
                            "html": "",
                            "response_time_ms": round((time.time() - start_time) * 1000.0, 2),
                            "error": f"Ignored non-text content-type: {content_type}"
                        }

                    # Stream with size limit protection
                    chunks = []
                    total_bytes = 0
                    async for chunk in response.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > MAX_RESPONSE_BYTES:
                            return {
                                "url": str(response.url),
                                "status_code": response.status_code,
                                "html": "",
                                "response_time_ms": round((time.time() - start_time) * 1000.0, 2),
                                "error": f"Response exceeded max size limit ({MAX_RESPONSE_BYTES // (1024*1024)}MB)"
                            }
                        chunks.append(chunk)

                    raw_content = b"".join(chunks)
                    # Decode text safely
                    try:
                        encoding = response.encoding or "utf-8"
                        text = raw_content.decode(encoding, errors="replace")
                    except Exception:
                        text = raw_content.decode("utf-8", errors="replace")

                    elapsed_ms = (time.time() - start_time) * 1000.0
                    return {
                        "url": str(response.url),
                        "status_code": response.status_code,
                        "html": text,
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

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")
        
        # 1. Base Meta Extraction
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        
        # 2. Extract Links for Graph Traversal (Same-origin preference)
        parsed_origin = urlparse(url).netloc
        discovered_links = []
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            full_url = urljoin(url, href)
            # Normalize and keep only http/https
            if full_url.startswith('http://') or full_url.startswith('https://'):
                # Prioritize same-domain crawling
                if urlparse(full_url).netloc == parsed_origin:
                    discovered_links.append(full_url)
        
        # Limit links per page to prevent combinatorial explosion
        discovered_links = list(dict.fromkeys(discovered_links))[:30]

        extracted_data: Dict[str, Any] = {}

        # 3. Custom CSS Selectors (if specified by operator)
        if custom_selectors:
            for field, selector in custom_selectors.items():
                match = soup.select(selector)
                if match:
                    if len(match) == 1:
                        extracted_data[field] = match[0].get_text(strip=True)
                    else:
                        extracted_data[field] = [m.get_text(strip=True) for m in match[:10]]
                else:
                    extracted_data[field] = None

        # 4. Intelligence-specific Extraction Engines
        if crawler_type == "ecommerce":
            extracted_data.update(self._extract_ecommerce(soup))
        elif crawler_type == "news":
            extracted_data.update(self._extract_news(soup))
        elif crawler_type == "schema":
            extracted_data.update(self._extract_json_ld(soup))
        else:
            extracted_data.update(self._extract_generic(soup))

        return {
            "title": title,
            "data": extracted_data,
            "discovered_links": discovered_links
        }

    def _extract_ecommerce(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract prices, SKUs, ratings, and stock status"""
        data = {}
        # Price detection regex heuristic
        price_match = soup.find(string=re.compile(r'[\$£€₹]\s*\d+([.,]\d{2})?'))
        if price_match:
            clean_price = re.search(r'[\$£€₹]?\s*(\d+([.,]\d{2})?)', price_match)
            if clean_price:
                data["price"] = clean_price.group(0).strip()

        # Common PDP selectors
        for selector in ['.price', '.product-price', '[data-price]', '#priceblock_ourprice', '.pdp-price', 'p.price_color']:
            el = soup.select_one(selector)
            if el:
                data["price"] = el.get_text(strip=True)
                break

        # Stock availability heuristic
        stock_text = soup.find(string=re.compile(r'(in stock|out of stock|available)', re.I))
        if stock_text:
            data["availability"] = stock_text.strip()
        
        # Rating heuristic
        rating_el = soup.select_one('.rating, .star-rating, [data-rating], .review-score, p.star-rating')
        if rating_el:
            classes = rating_el.get('class', [])
            data["rating"] = ' '.join(classes) if isinstance(classes, list) else str(classes)

        return data

    def _extract_news(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract article headlines, author, publication timestamp, and sentiment"""
        data = {}
        # Headline
        h1 = soup.find('h1')
        if h1:
            data["headline"] = h1.get_text(strip=True)

        # Author
        author_el = soup.select_one('[rel="author"], .author, .byline, .author-name')
        if author_el:
            data["author"] = author_el.get_text(strip=True)

        # Main paragraph body for NLP sentiment
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 40]
        full_text = " ".join(paragraphs[:8])
        if full_text:
            blob = TextBlob(full_text)
            data["sentiment_polarity"] = round(blob.sentiment.polarity, 3)
            data["sentiment_subjectivity"] = round(blob.sentiment.subjectivity, 3)
            data["summary_sample"] = full_text[:280] + "..." if len(full_text) > 280 else full_text

        return data

    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract and parse Schema.org JSON-LD structured script elements"""
        data = {"schemas": []}
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                if script.string:
                    parsed = json.loads(script.string)
                    data["schemas"].append(parsed)
            except Exception:
                continue
        return data

    def _extract_generic(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Default generic extractor (headings, meta description, word count)"""
        data = {}
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc and meta_desc.get('content'):
            data["description"] = meta_desc['content'].strip()

        # Extract top 3 H2 subheaders
        h2s = [h.get_text(strip=True) for h in soup.find_all('h2') if h.get_text(strip=True)]
        if h2s:
            data["subheadings"] = h2s[:3]

        text = soup.get_text()
        words = len(text.split())
        data["word_count"] = words
        return data

crawler_engine = CrawlerEngine()
