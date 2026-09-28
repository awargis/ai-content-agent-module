from typing import List
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from .models import Article, SourceConfig
from .utils import (
    canonical_key,
    content_hash,
    normalize_text,
    normalize_url,
    parse_date,
)


USER_AGENT = (
    "AIContentAgent/1.0 (+https://github.com/; responsible automated collector)"
)


class Scraper:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def collect(self, source: SourceConfig) -> List[Article]:
        if source.type == "rss":
            return self._collect_rss(source)
        if source.type == "website":
            return self._collect_website(source)
        raise ValueError(f"Unsupported source type: {source.type}")

    def _collect_rss(self, source: SourceConfig) -> List[Article]:
        response = self.session.get(source.url, timeout=self.timeout)
        response.raise_for_status()

        parsed = feedparser.parse(response.content)
        articles = []

        for entry in parsed.entries[: source.max_items]:
            url = normalize_url(
                entry.get("link")
                or entry.get("id")
                or source.url
            )
            title = normalize_text(entry.get("title", ""))
            description = normalize_text(
                entry.get("summary") or entry.get("description") or ""
            )

            content_parts = []
            for item in entry.get("content", []) or []:
                value = item.get("value", "")
                if value:
                    content_parts.append(
                        BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
                    )
            content = normalize_text(" ".join(content_parts)) or description

            author = normalize_text(
                entry.get("author")
                or entry.get("dc_creator")
                or ""
            )

            published_raw = (
                entry.get("published")
                or entry.get("updated")
                or entry.get("created")
            )

            image_url = ""
            media_content = entry.get("media_content", []) or []
            if media_content:
                image_url = media_content[0].get("url", "") or ""

            media_thumbnail = entry.get("media_thumbnail", []) or []
            if not image_url and media_thumbnail:
                image_url = media_thumbnail[0].get("url", "") or ""

            article_id = canonical_key(source.url, url)
            c_hash = content_hash(title, url, content)

            articles.append(
                Article(
                    article_id=article_id,
                    source_name=source.name,
                    source_type=source.type,
                    source_url=source.url,
                    category=source.category,
                    priority=source.priority,
                    title=title,
                    url=url,
                    description=description,
                    content=content,
                    author=author,
                    published_at=parse_date(published_raw),
                    image_url=normalize_url(image_url),
                    source_item_id=normalize_text(
                        entry.get("id") or entry.get("guid") or ""
                    ),
                    content_hash=c_hash,
                )
            )

        return articles

    def _collect_website(self, source: SourceConfig) -> List[Article]:
        selectors = source.selectors or {}
        response = self.session.get(source.url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        article_nodes = soup.select(selectors.get("article", "article"))
        if not article_nodes:
            article_nodes = [soup]

        articles = []

        for node in article_nodes[: source.max_items]:
            title_node = node.select_one(selectors.get("title", "h1"))
            content_node = node.select_one(selectors.get("content", "article"))
            date_node = node.select_one(selectors.get("date", "time"))
            author_node = node.select_one(selectors.get("author", "[rel='author']"))
            image_node = node.select_one(selectors.get("image", "img"))

            title = normalize_text(
                title_node.get_text(" ", strip=True) if title_node else ""
            )
            content = normalize_text(
                content_node.get_text(" ", strip=True)
                if content_node
                else node.get_text(" ", strip=True)
            )

            if not title:
                continue

            link_node = node.select_one("a[href]")
            url = normalize_url(
                urljoin(
                    source.url,
                    link_node.get("href", "") if link_node else source.url,
                )
            )

            published_raw = ""
            if date_node:
                published_raw = date_node.get("datetime") or date_node.get_text(" ", strip=True)

            author = ""
            if author_node:
                author = normalize_text(author_node.get_text(" ", strip=True))

            image_url = ""
            if image_node:
                image_url = urljoin(source.url, image_node.get("src", ""))

            article_id = canonical_key(source.url, url)
            c_hash = content_hash(title, url, content)

            articles.append(
                Article(
                    article_id=article_id,
                    source_name=source.name,
                    source_type=source.type,
                    source_url=source.url,
                    category=source.category,
                    priority=source.priority,
                    title=title,
                    url=url,
                    description="",
                    content=content,
                    author=author,
                    published_at=parse_date(published_raw),
                    image_url=normalize_url(image_url),
                    source_item_id=url,
                    content_hash=c_hash,
                )
            )

        return articles
