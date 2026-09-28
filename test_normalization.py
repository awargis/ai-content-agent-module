from src.utils import normalize_text, normalize_url, parse_date


def test_normalize_text():
    assert normalize_text("  Hello   <b>world</b>  ") == "Hello <b>world</b>"


def test_normalize_url_removes_fragment():
    assert normalize_url("HTTPS://Example.COM/news#section") == "https://example.com/news"


def test_parse_date_to_utc():
    value = parse_date("2026-09-28 07:00:00")
    assert value is not None
    assert value.endswith("+00:00")
