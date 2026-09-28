import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from .models import SourceConfig

load_dotenv()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_settings() -> dict:
    return {
        "webhook_url": os.getenv("WEBHOOK_URL", "").strip(),
        "webhook_secret": os.getenv("WEBHOOK_SECRET", "").strip(),
        "timeout": int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
        "max_articles_per_source": int(os.getenv("MAX_ARTICLES_PER_SOURCE", "10")),
        "state_file": os.getenv(
            "STATE_FILE",
            str(project_root() / "data" / "state.json"),
        ),
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
    }


def load_sources(path: str | None = None) -> List[SourceConfig]:
    source_path = Path(path) if path else project_root() / "config" / "sources.json"
    data = json.loads(source_path.read_text(encoding="utf-8"))
    sources = []

    for item in data.get("sources", []):
        source = SourceConfig(
            name=item["name"],
            type=item["type"].lower(),
            url=item["url"],
            category=item.get("category", "general"),
            priority=int(item.get("priority", 5)),
            enabled=bool(item.get("enabled", True)),
            max_items=int(item.get("max_items", 10)),
            selectors=item.get("selectors"),
        )
        if source.enabled:
            sources.append(source)

    return sources
