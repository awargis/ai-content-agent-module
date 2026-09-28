import json
import sys
import time
from pathlib import Path

import requests

from .config import load_settings, load_sources
from .scraper import Scraper
from .state import StateStore
from .utils import get_logger, utc_now_iso


def validate_settings(settings: dict) -> None:
    if not settings["webhook_url"]:
        raise RuntimeError("WEBHOOK_URL is not configured.")
    if not settings["webhook_secret"]:
        raise RuntimeError("WEBHOOK_SECRET is not configured.")


def send_webhook(
    session: requests.Session,
    url: str,
    secret: str,
    payload: dict,
    timeout: int,
    logger,
    retries: int = 3,
) -> None:
    headers = {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
        "X-Agent-Name": "ai-content-agent",
        "X-Agent-Version": "1.0.0",
    }

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = session.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )

            if 200 <= response.status_code < 300:
                logger.info(
                    "Webhook accepted article_id=%s status=%s",
                    payload["article_id"],
                    response.status_code,
                )
                return

            # Retry temporary server/rate-limit errors.
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(
                    f"Temporary webhook error {response.status_code}: {response.text[:300]}"
                )

            response.raise_for_status()

        except (requests.RequestException, OSError) as exc:
            last_error = exc
            if attempt < retries:
                delay = 2 ** (attempt - 1)
                logger.warning(
                    "Webhook attempt %s/%s failed: %s; retrying in %ss",
                    attempt,
                    retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
            else:
                break

    raise RuntimeError(f"Webhook failed after {retries} attempts: {last_error}")


def run() -> int:
    settings = load_settings()
    logger = get_logger("collector", settings["log_level"])

    try:
        validate_settings(settings)
        sources = load_sources()

        logger.info("Starting collector")
        logger.info("Loaded %s enabled sources", len(sources))

        if not sources:
            logger.warning("No enabled sources found. Edit config/sources.json.")
            return 0

        state = StateStore(settings["state_file"])
        scraper = Scraper(settings["timeout"])
        webhook_session = requests.Session()

        candidates = []
        for source in sources:
            try:
                articles = scraper.collect(source)
                logger.info(
                    "Source '%s': collected %s candidates",
                    source.name,
                    len(articles),
                )
                candidates.extend(articles)
            except Exception as exc:
                logger.exception(
                    "Source '%s' failed: %s",
                    source.name,
                    exc,
                )

        # Deduplicate inside this run first.
        unique = []
        seen_ids = set()
        seen_hashes = set()

        for article in candidates:
            if not article.title or not article.url:
                continue
            if article.article_id in seen_ids or article.content_hash in seen_hashes:
                continue

            seen_ids.add(article.article_id)
            seen_hashes.add(article.content_hash)
            unique.append(article)

        logger.info(
            "Collected %s candidates; %s unique in this run",
            len(candidates),
            len(unique),
        )

        new_articles = [
            article
            for article in unique
            if not state.has_id(article.article_id)
            and not state.has_hash(article.content_hash)
        ]

        logger.info(
            "%s new articles after persistent deduplication",
            len(new_articles),
        )

        sent = 0
        failed = 0
        collected_at = utc_now_iso()

        for article in new_articles:
            payload = article.to_payload(collected_at)

            try:
                send_webhook(
                    webhook_session,
                    settings["webhook_url"],
                    settings["webhook_secret"],
                    payload,
                    settings["timeout"],
                    logger,
                )
                state.add(article.article_id, article.content_hash)
                sent += 1
            except Exception as exc:
                failed += 1
                logger.error(
                    "Failed to send article '%s': %s",
                    article.title[:100],
                    exc,
                )

        state.save()

        logger.info(
            "Collector completed: sent=%s failed=%s total_new=%s",
            sent,
            failed,
            len(new_articles),
        )

        # Fail the Action only if something that was supposed to be delivered
        # could not be delivered. This makes GitHub Actions visibly red.
        return 1 if failed else 0

    except Exception as exc:
        logger.exception("Collector failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(run())
