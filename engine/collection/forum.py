"""
T-P2-03 - Forum / complaint-site connector.

HTTP + selectolax, robots.txt-respecting, externalised selectors.
Guards: EC-C-09, ARCH §18
"""

import logging
from datetime import datetime, timezone
from typing import Any, Iterator
from pathlib import Path
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

from engine.collection.base import BaseConnector

logger = logging.getLogger(__name__)


class ForumConnector(BaseConnector):
    """
    Collects threads/reviews from generic forums or complaint sites using CSS selectors.
    """
    
    def __init__(
        self,
        brand: str,
        data_dir: Path,
        base_url: str,
        selectors: dict[str, str],
        max_pages: int = 100,
    ):
        super().__init__(source="forum", brand=brand, data_dir=data_dir, max_pages=max_pages)
        self.base_url = base_url
        self.selectors = selectors
        self.client = httpx.Client(timeout=30.0)
        self.last_request = 0.0
        
        # Parse domain for robots.txt
        parsed = urlparse(self.base_url)
        self.domain = f"{parsed.scheme}://{parsed.netloc}"

    def __del__(self):
        try:
            self.client.close()
        except:
            pass

    def _check_robots_txt(self) -> bool:
        """
        Check if the site allows crawling by fetching robots.txt.
        This is a basic implementation (EC-C-09).
        """
        try:
            resp = self.client.get(f"{self.domain}/robots.txt")
            if resp.status_code == 200:
                # Basic check - if it says Disallow: / we skip
                if "Disallow: /" in resp.text:
                    logger.warning(f"robots.txt disallows crawling for {self.domain}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to fetch robots.txt for {self.domain}: {e}")
            return False

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        # Respect robots.txt (EC-C-09)
        if not self._check_robots_txt():
            logger.info(f"Skipping {self.brand} on {self.domain} due to robots.txt")
            return

        page = 1
        yielded = 0
        seen_hashes = set()
        
        url_template = self.selectors.get("url_template", self.base_url + "?page={page}")
        
        while page <= self.max_pages:
            url = url_template.replace("{page}", str(page))
            self.last_request = self.enforce_politeness(self.last_request, min_interval=2.0)
            
            try:
                logger.info(f"ForumConnector [{self.brand}]: fetching {url}")
                resp = self.client.get(url)
                
                # Handle Cloudflare/Walls
                if resp.status_code in [403, 429, 503] or "cloudflare" in resp.text.lower():
                    logger.warning(f"Walled site detected (Cloudflare/Login) at {url}. Documenting gap.")
                    break
                    
                resp.raise_for_status()
                html = resp.text
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                break
                
            parser = HTMLParser(html)
            
            # Selectors
            item_sel = self.selectors.get("item", ".item")
            id_sel = self.selectors.get("id", "id") # attribute name
            body_sel = self.selectors.get("body", ".body")
            author_sel = self.selectors.get("author", ".author")
            time_sel = self.selectors.get("time", ".time")
            
            items = parser.css(item_sel)
            if not items:
                logger.info(f"No items found on page {page}")
                break
                
            # Loop detection by checking raw HTML of items
            raw_htmls = [n.html for n in items]
            self.check_page_loop(raw_htmls, seen_hashes)
            
            for node in items:
                # Extract fields
                source_id = node.attributes.get(id_sel)
                if not source_id:
                    continue
                    
                body_node = node.css_first(body_sel)
                body = body_node.text(strip=True) if body_node else ""
                
                author_node = node.css_first(author_sel)
                author = author_node.text(strip=True) if author_node else "unknown"
                
                time_node = node.css_first(time_sel)
                time_str = time_node.text(strip=True) if time_node else ""
                
                payload = {
                    "_source": self.source,
                    "_brand": self.brand,
                    "id": source_id,
                    "body": body,
                    "author": author,
                    "time_str": time_str,
                    "url": url,
                }
                
                yield payload
                yielded += 1
                if limit and yielded >= limit:
                    return
                    
            page += 1


def normalise_forum_payload(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> "Verbatim":
    from engine.store.verbatim import make_verbatim
    # Use standard datetime parsing for simple formats to avoid extra dependency if possible
    # We'll just use a basic fallback
    
    source = raw.get("_source", "forum")
    brand = raw.get("_brand", "unknown")
    source_id = raw.get("id")
    if not source_id:
        raise ValueError("Missing id in Forum payload")
        
    text_raw = raw.get("body", "")
    author = raw.get("author", "unknown")
    
    dt = datetime.now(tz=timezone.utc)
    # We skip complex date parsing for now, or just use UTC now if not provided nicely
        
    return make_verbatim(
        source=source,
        source_id=source_id,
        brand=brand,
        run_id=run_id,
        raw_payload_ref=raw_payload_ref,
        text_raw=text_raw,
        rating=None,
        review_date=dt,
        meta={"author": author, "url": raw.get("url")}
    )
