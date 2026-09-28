from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class SourceConfig:
    name: str
    type: str
    url: str
    category: str = "general"
    priority: int = 5
    enabled: bool = True
    max_items: int = 10
    selectors: Optional[Dict[str, str]] = None


@dataclass
class Article:
    article_id: str
    source_name: str
    source_type: str
    source_url: str
    category: str
    priority: int
    title: str
    url: str
    description: str = ""
    content: str = ""
    author: str = ""
    published_at: Optional[str] = None
    image_url: str = ""
    source_item_id: str = ""
    content_hash: str = ""

    def to_payload(self, collected_at: str) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "event": "content.discovered",
            "article_id": self.article_id,
            "source": {
                "name": self.source_name,
                "type": self.source_type,
                "url": self.source_url,
                "category": self.category,
                "priority": self.priority,
            },
            "article": {
                "title": self.title,
                "url": self.url,
                "description": self.description,
                "content": self.content,
                "author": self.author,
                "published_at": self.published_at,
                "image_url": self.image_url,
            },
            "metadata": {
                "collected_at": collected_at,
                "language": "en",
                "content_hash": self.content_hash,
                "source_item_id": self.source_item_id,
            },
            "pipeline": {
                "agent": "ai-content-agent",
                "module": "01-source-collector",
                "version": "1.0.0",
            },
        }
