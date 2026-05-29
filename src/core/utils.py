import re


_JSON_BLOCK_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def strip_markdown_json(text: str) -> str:
    return re.sub(_JSON_BLOCK_PATTERN, "", text.strip()).strip()
