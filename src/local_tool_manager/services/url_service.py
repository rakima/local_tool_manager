from __future__ import annotations

import re
from urllib.parse import quote_plus


PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def extract_placeholders(url: str) -> list[str]:
    return list(dict.fromkeys(PLACEHOLDER_PATTERN.findall(url)))


def render_url(url: str, parameters: dict[str, str]) -> str:
    required = extract_placeholders(url)
    missing = [name for name in required if name not in parameters]
    if missing:
        raise ValueError("URLパラメータが不足しています: " + ", ".join(missing))
    for name in required:
        url = url.replace("{" + name + "}", quote_plus(parameters[name]))
    return url

