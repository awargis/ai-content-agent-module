from src.utils import canonical_key, content_hash


def test_same_source_and_url_same_id():
    a = canonical_key("https://example.com/feed", "https://example.com/a#top")
    b = canonical_key("https://example.com/feed", "https://example.com/a")
    assert a == b


def test_different_articles_have_different_ids():
    a = canonical_key("https://example.com/feed", "https://example.com/a")
    b = canonical_key("https://example.com/feed", "https://example.com/b")
    assert a != b


def test_content_hash_is_stable():
    a = content_hash("Title", "https://example.com/a", "Hello world")
    b = content_hash("Title", "https://example.com/a", "Hello world")
    assert a == b
