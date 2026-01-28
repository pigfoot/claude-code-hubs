#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Confluence URL Resolver

Decode and resolve various Confluence URL formats to page IDs.

Supported formats:
- Short URLs: https://site.atlassian.net/wiki/x/2oEBfw
- Full URLs: https://site.atlassian.net/wiki/spaces/SPACE/pages/123456789/Title
- Direct page IDs: 123456789

Usage:
    python url_resolver.py "https://site.atlassian.net/wiki/x/2oEBfw"
    python url_resolver.py "https://site.atlassian.net/wiki/spaces/SPACE/pages/123456/Title"
    python url_resolver.py "123456789"
"""

import base64
import re
import sys
from typing import Dict, Union


def decode_tiny_url(tiny_code: str) -> int:
    """
    Decode Confluence TinyUI short URL to page ID.

    Confluence short URLs use Base64 encoding with URL-safe characters
    and little-endian byte order for the page ID.

    Example: /wiki/x/2oEBfw -> page ID 2130805210

    Args:
        tiny_code: The code from /wiki/x/{code}

    Returns:
        Page ID as integer

    Raises:
        ValueError: If decoding fails
    """
    try:
        # Add padding if needed (Base64 requires length divisible by 4)
        padded = tiny_code + "=="

        # Convert URL-safe Base64 to standard Base64
        # URL-safe uses: - instead of +, _ instead of /
        standard_b64 = padded.replace("-", "+").replace("_", "/")

        # Decode Base64
        decoded_bytes = base64.b64decode(standard_b64)

        # Convert bytes to integer (little-endian)
        # Confluence uses little-endian byte order for page IDs
        page_id = int.from_bytes(decoded_bytes, "little")

        return page_id
    except Exception as e:
        raise ValueError(f"Failed to decode tiny URL '{tiny_code}': {e}")


def resolve_confluence_url(url_or_id: Union[str, int]) -> Dict[str, str]:
    """
    Resolve various Confluence URL formats to page ID.

    Supported formats:
    - Short URL: https://site.atlassian.net/wiki/x/ZQGBfg
    - Full URL: https://site.atlassian.net/wiki/spaces/SPACE/pages/123456789/Title
    - Direct page ID: 123456789 (string or int)

    Args:
        url_or_id: Confluence URL or page ID

    Returns:
        Dict with keys:
        - type: "page_id" or "unknown"
        - value: The resolved page ID (as string) or original value

    Examples:
        >>> resolve_confluence_url("https://site.atlassian.net/wiki/x/2oEBfw")
        {'type': 'page_id', 'value': '2130805210'}

        >>> resolve_confluence_url("https://site.atlassian.net/wiki/spaces/SPACE/pages/123456/Title")
        {'type': 'page_id', 'value': '123456'}

        >>> resolve_confluence_url("123456789")
        {'type': 'page_id', 'value': '123456789'}

        >>> resolve_confluence_url(123456789)
        {'type': 'page_id', 'value': '123456789'}
    """
    # Convert to string if integer
    if isinstance(url_or_id, int):
        return {"type": "page_id", "value": str(url_or_id)}

    url_str = str(url_or_id).strip()

    # Pattern 1: Direct numeric page ID
    if url_str.isdigit():
        return {"type": "page_id", "value": url_str}

    # Pattern 2: Short URL - /wiki/x/{code}
    short_url_pattern = r"/wiki/x/([A-Za-z0-9_-]+)"
    match = re.search(short_url_pattern, url_str)
    if match:
        tiny_code = match.group(1)
        try:
            page_id = decode_tiny_url(tiny_code)
            return {"type": "page_id", "value": str(page_id)}
        except ValueError as e:
            # Decoding failed, return as unknown
            return {"type": "unknown", "value": url_str, "error": str(e)}

    # Pattern 3: Full URL - /wiki/spaces/{space}/pages/{id}/{title}
    full_url_pattern = r"/wiki/spaces/[^/]+/pages/(\d+)"
    match = re.search(full_url_pattern, url_str)
    if match:
        page_id = match.group(1)
        return {"type": "page_id", "value": page_id}

    # Pattern 4: Alternative full URL - /pages/{id}/{title}
    alt_url_pattern = r"/pages/(\d+)"
    match = re.search(alt_url_pattern, url_str)
    if match:
        page_id = match.group(1)
        return {"type": "page_id", "value": page_id}

    # Unknown format
    return {"type": "unknown", "value": url_str}


def main():
    """CLI interface for URL resolution"""
    if len(sys.argv) < 2:
        print("Usage: python url_resolver.py <url_or_page_id>")
        print()
        print("Examples:")
        print("  python url_resolver.py 'https://site.atlassian.net/wiki/x/2oEBfw'")
        print(
            "  python url_resolver.py 'https://site.atlassian.net/wiki/spaces/SPACE/pages/123456/Title'"
        )
        print("  python url_resolver.py '123456789'")
        sys.exit(1)

    input_value = sys.argv[1]
    result = resolve_confluence_url(input_value)

    # Pretty print result
    import json

    print(json.dumps(result, indent=2))

    # Exit code
    if result["type"] == "unknown":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
