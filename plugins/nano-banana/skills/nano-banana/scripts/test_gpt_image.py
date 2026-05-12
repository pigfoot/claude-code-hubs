#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["openai", "pillow"]
# ///
"""
Test gpt-image-2 via images.generate() and images.edit() on the RONE proxy.

Tests:
  T1: Basic generation — confirm /images/generations works
  T2: Seed consistency — same seed produces same hash?
  T3: Seed variance — different seeds produce different images?
  T4: /images/edits — confirm edit endpoint works with a reference image
  T5: TrendLife featured — logo as image param to /images/edits (skipped if logo missing)

Usage:
    RDSEC_API_KEY=... IMAGE_GEN_BASE_URL=... uv run test_gpt_image.py
"""

import hashlib
import io
import os
import sys
from pathlib import Path

from openai import OpenAI
from PIL import Image as PILImage

PROMPT = "A bright red apple on a white table, studio lighting, photorealistic"
MODEL = "gpt-image-2"
SEED = 42

LOGO_PATH = Path(__file__).parent.parent / "assets/logos/trendlife-2026-logo-light.png"


def hash_b64(b64_str: str) -> str:
    return hashlib.sha256(b64_str.encode()).hexdigest()[:16]


def make_test_image_bytes() -> bytes:
    img = PILImage.new("RGB", (64, 64), color=(100, 149, 237))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate(client: OpenAI, seed=None, extra_body=None) -> str:
    kwargs = dict(
        model=MODEL,
        prompt=PROMPT,
        n=1,
        size="1024x1024",
        quality="low",
        response_format="b64_json",
    )
    if extra_body:
        kwargs["extra_body"] = extra_body

    resp = client.images.generate(**kwargs)

    if not resp.data or not resp.data[0].b64_json:
        print("ERROR: empty response", file=sys.stderr)
        sys.exit(1)

    return resp.data[0].b64_json


def edit(client: OpenAI, image_bytes: bytes, image_name: str = "ref.png") -> str:
    resp = client.images.edit(
        model=MODEL,
        image=(image_name, image_bytes, "image/png"),
        prompt=PROMPT,
        n=1,
        size="1024x1024",
        quality="low",
    )

    if not resp.data or not resp.data[0].b64_json:
        print("ERROR: empty response", file=sys.stderr)
        sys.exit(1)

    return resp.data[0].b64_json


def main():
    api_key = os.environ.get("RDSEC_API_KEY")
    base_url = os.environ.get("IMAGE_GEN_BASE_URL")

    if not api_key or not base_url:
        print(
            "Error: RDSEC_API_KEY and IMAGE_GEN_BASE_URL must be set", file=sys.stderr
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)

    print(f"Model: {MODEL}")
    print(f"Endpoint: {base_url}")
    print()

    # T1: Basic generation
    print("T1: Basic generation (no seed)...")
    b64_1 = generate(client)
    h1 = hash_b64(b64_1)
    print(f"  OK  hash={h1}  len={len(b64_1)}")
    print()

    # T2: Seed consistency - run twice with same seed
    print(f"T2: Seed consistency (seed={SEED}, run twice)...")
    b64_s1 = generate(client, extra_body={"seed": SEED})
    h_s1 = hash_b64(b64_s1)
    print(f"  Run 1: hash={h_s1}")

    b64_s2 = generate(client, extra_body={"seed": SEED})
    h_s2 = hash_b64(b64_s2)
    print(f"  Run 2: hash={h_s2}")

    if h_s1 == h_s2:
        print(f"  PASS: seed={SEED} produces identical images")
    else:
        print(f"  FAIL: seed={SEED} produces different images (seed has no effect)")
    print()

    # T3: Different seeds should differ
    print("T3: Seed variance (seed=42 vs seed=99)...")
    b64_a = generate(client, extra_body={"seed": 42})
    b64_b = generate(client, extra_body={"seed": 99})
    h_a = hash_b64(b64_a)
    h_b = hash_b64(b64_b)
    print(f"  seed=42: {h_a}")
    print(f"  seed=99: {h_b}")
    if h_a != h_b:
        print("  PASS: different seeds produce different images")
    else:
        print(
            "  NOTE: different seeds produced same image (may be coincidence or no effect)"
        )
    print()

    # T4: /images/edits with synthetic reference image
    print("T4: /images/edits with synthetic reference image...")
    test_image_bytes = make_test_image_bytes()
    try:
        b64_edit = edit(client, test_image_bytes)
        h_edit = hash_b64(b64_edit)
        print(f"  OK  hash={h_edit}  len={len(b64_edit)}")
        print("  PASS: /images/edits endpoint works")
    except Exception as e:
        print(f"  FAIL: {e}")
    print()

    # T5: TrendLife featured — logo as image param
    print("T5: TrendLife featured (logo as reference image)...")
    if not LOGO_PATH.exists():
        print(f"  SKIP: logo not found at {LOGO_PATH}")
    else:
        logo_bytes = LOGO_PATH.read_bytes()
        trendlife_prompt = (
            "Product Launch 2026\n\n"
            "This is a title/cover slide for TrendLife (Trend Micro presentations).\n"
            "Create a professional cover design that incorporates the TrendLife logo provided as reference image.\n"
            "Use TrendLife brand colors:\n"
            "- Trend Red (#D71920) for title and accents\n"
            "- Black (#000000) for text, white (#FFFFFF) for backgrounds\n"
            "IMPORTANT: Use the exact logo from the reference image.\n"
            "Position it prominently. Keep the design clean and professional."
        )
        try:
            resp = client.images.edit(
                model=MODEL,
                image=("trendlife-logo.png", logo_bytes, "image/png"),
                prompt=trendlife_prompt,
                n=1,
                size="1024x1024",
                quality="low",
            )
            if resp.data and resp.data[0].b64_json:
                h_tl = hash_b64(resp.data[0].b64_json)
                print(f"  OK  hash={h_tl}  len={len(resp.data[0].b64_json)}")
                print("  PASS: TrendLife featured via /images/edits works")
            else:
                print("  FAIL: empty response")
        except Exception as e:
            print(f"  FAIL: {e}")


if __name__ == "__main__":
    main()
