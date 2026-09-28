import hashlib
import html
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from dateutil import parser as date_parser


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False
    return logger


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    # Remove fragments. Keep query parameters because some sites use them
    # as meaningful article identifiers.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def canonical_key(source_url: str, article_url: str) -> str:
    raw = f"{normalize_url(source_url)}|{normalize_url(article_url)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def content_hash(title: str, url: str, content: str) -> str:
    raw = "|".join(
        [
            normalize_text(title).lower(),
            normalize_url(url),
            normalize_text(content).lower(),
        ]
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
