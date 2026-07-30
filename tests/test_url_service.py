import pytest

from local_tool_manager.services.url_service import extract_placeholders, render_url


def test_extracts_unique_placeholders_in_order():
    url = "https://example.com/{project}?q={keyword}&again={keyword}"
    assert extract_placeholders(url) == ["project", "keyword"]


def test_replaces_and_url_encodes_parameters():
    url = render_url(
        "https://example.com/search?q={keyword}&name={name}",
        {"keyword": "日本語 test", "name": "A&B"},
    )
    assert url == "https://example.com/search?q=%E6%97%A5%E6%9C%AC%E8%AA%9E+test&name=A%26B"


def test_missing_parameter_is_rejected():
    with pytest.raises(ValueError):
        render_url("https://example.com/{key}", {})

