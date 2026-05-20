#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["openai", "pillow", "python-dotenv"]
# ///
"""
generate_images.py - Unified image generation with progress tracking

IMPORTANT: This script MUST be run with uv:
    uv run generate_images.py --config slides_config.json

DO NOT run with plain python (dependencies will not be found)

Usage:
    uv run generate_images.py --config <config_file>

Config format:
    {
        "slides": [
            {"number": 1, "prompt": "...", "style": "professional", "temperature": 0.8, "seed": 42},
            {"number": 2, "prompt": "...", "style": "data-viz"},
            {"number": 3, "prompt": "Add a border", "reference_image": "./source.png"}
        ],
        "output_dir": "./output/",
        "format": "webp",
        "quality": 90,
        "temperature": 1.0,
        "seed": 12345
    }

Temperature:
    - Range: 0.0 to 2.0
    - Default: 1.0
    - Lower values (0.0-0.5): More deterministic and consistent
    - Higher values (0.7-1.0+): More random and creative
    - Priority: slide.temperature > config.temperature > 1.0
    - NOT supported for gpt-image-2 (ignored with warning)

Seed:
    - Integer value for reproducible generation
    - Same seed + same prompt + same temperature = same image
    - Default: None (random seed each time)
    - Priority: slide.seed > config.seed > None
    - NOT supported for gpt-image-2 (ignored with warning)

reference_image:
    - Optional path to a source image for gpt-image-2 editing mode
    - Must be a relative path (resolved from working directory)
    - Only used when IMAGE_GEN_MODEL=gpt-image-2

Note: Model is set via IMAGE_GEN_MODEL environment variable, not in config.

Model routing:
    - gpt-image-2 + no reference_image → POST /images/generations (quality=low)
    - gpt-image-2 + reference_image    → POST /images/edits (multipart, quality=low)
    - any other model                  → chat.completions with response_modalities=["IMAGE"]

Required environment variables:
    IMAGE_GEN_BASE_URL  - OpenAI-compatible endpoint URL (must include /v1 suffix)
    RDSEC_API_KEY       - API key / JWT token

Output files (in system temp directory):
    - Progress: {temp_dir}/nano-banana-progress.json
    - Results: {temp_dir}/nano-banana-results.json
"""

import base64
import json
import sys
import os
import io
import tempfile
import time
from pathlib import Path

try:
    from datetime import datetime, UTC
except ImportError:
    from datetime import datetime, timezone

    UTC = timezone.utc
from typing import Dict, List, Tuple, Optional

from openai import OpenAI
from PIL import Image as PILImage

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Progress and results file paths (cross-platform)
TEMP_DIR = Path(tempfile.gettempdir())
PROGRESS_FILE = TEMP_DIR / "nano-banana-progress.json"
RESULTS_FILE = TEMP_DIR / "nano-banana-results.json"

GPT_IMAGE_2 = "gpt-image-2"


def validate_output_dir(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        print(
            f"Error: output_dir must be relative path, got: {path_str}\n"
            f"Use './dirname/' instead for cross-platform compatibility.",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


def load_config(config_path: str) -> Dict:
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)

    if "slides" not in config or not isinstance(config["slides"], list):
        print("Error: Config must contain 'slides' array", file=sys.stderr)
        sys.exit(1)

    if not config["slides"]:
        print("Error: 'slides' array is empty", file=sys.stderr)
        sys.exit(1)

    if "output_dir" not in config:
        print("Error: Config must contain 'output_dir'", file=sys.stderr)
        sys.exit(1)

    validate_output_dir(config["output_dir"])

    if "temperature" in config:
        temp = config["temperature"]
        if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 2.0:
            print(
                f"Error: Global temperature must be between 0.0 and 2.0, got: {temp}",
                file=sys.stderr,
            )
            sys.exit(1)

    if "seed" in config:
        seed = config["seed"]
        if not isinstance(seed, int):
            print(
                f"Error: Global seed must be an integer, got: {seed}", file=sys.stderr
            )
            sys.exit(1)

    for i, slide in enumerate(config["slides"]):
        if "number" not in slide:
            print(f"Error: Slide {i} missing 'number' field", file=sys.stderr)
            sys.exit(1)
        if "prompt" not in slide:
            print(f"Error: Slide {i} missing 'prompt' field", file=sys.stderr)
            sys.exit(1)

        if "temperature" in slide:
            temp = slide["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 2.0:
                print(
                    f"Error: Slide {i} temperature must be between 0.0 and 2.0, got: {temp}",
                    file=sys.stderr,
                )
                sys.exit(1)

        if "seed" in slide:
            seed = slide["seed"]
            if not isinstance(seed, int):
                print(
                    f"Error: Slide {i} seed must be an integer, got: {seed}",
                    file=sys.stderr,
                )
                sys.exit(1)

        if "reference_image" in slide:
            ref = slide["reference_image"]
            if not isinstance(ref, str):
                print(
                    f"Error: Slide {i} reference_image must be a string path",
                    file=sys.stderr,
                )
                sys.exit(1)
            if Path(ref).is_absolute():
                print(
                    f"Error: Slide {i} reference_image must be a relative path, got: {ref}",
                    file=sys.stderr,
                )
                sys.exit(1)

    return config


def write_progress(
    current: int,
    total: int,
    status: str,
    completed: List[str],
    failed: List[int],
    started_at: str,
) -> None:
    try:
        progress = {
            "current": current,
            "total": total,
            "status": status,
            "completed": completed,
            "failed": failed,
            "started_at": started_at,
            "updated_at": datetime.now(UTC).isoformat() + "Z",
        }
        temp_file = PROGRESS_FILE.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(progress, f, indent=2)
        temp_file.replace(PROGRESS_FILE)
    except Exception as e:
        print(f"Warning: Failed to write progress file: {e}", file=sys.stderr)


def write_results(
    completed: List[Dict], failed: List[int], errors: List[Dict], started_at: str
) -> None:
    try:
        completed_at = datetime.now(UTC).isoformat() + "Z"
        started_dt = datetime.fromisoformat(started_at.rstrip("Z"))
        completed_dt = datetime.fromisoformat(completed_at.rstrip("Z"))
        duration = (completed_dt - started_dt).total_seconds()

        results = {
            "completed": len(completed),
            "failed": len(failed),
            "total": len(completed) + len(failed),
            "outputs": completed,
            "errors": errors,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": int(duration),
        }

        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2)

    except Exception as e:
        print(f"Error: Failed to write results file: {e}", file=sys.stderr)
        sys.exit(1)


def generate_seed() -> int:
    time.sleep(0.001)
    timestamp_ns = time.time_ns()
    return int(timestamp_ns % 2147483647)


def _load_logo_base64(logo_path: Path) -> Optional[str]:
    """Load logo image as base64 string, returning None on failure."""
    try:
        with open(logo_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            if "version https://git-lfs.github.com" in first_line:
                print(
                    "Error: Logo file is a Git LFS pointer, not the actual image.",
                    file=sys.stderr,
                )
                print(
                    "Please install Git LFS and run: git lfs pull",
                    file=sys.stderr,
                )
                return None
    except Exception:
        pass  # binary file, OK

    try:
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Error: Failed to load logo image: {e}", file=sys.stderr)
        return None


def _extract_image_bytes(response) -> Optional[bytes]:
    """Extract image bytes from chat.completions response.

    LiteLLM returns the image in message.images (non-standard field).
    Falls back to content list for compatibility.
    """
    msg = response.choices[0].message
    raw = msg.model_dump()

    # Primary: LiteLLM non-standard message.images field
    images = raw.get("images") or []
    for img_item in images:
        url = img_item.get("image_url", {}).get("url", "")
        if url.startswith("data:image"):
            return base64.b64decode(url.split(",", 1)[1])

    # Fallback: content list (standard multimodal format)
    if isinstance(msg.content, list):
        for part in msg.content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url", "")
                if url.startswith("data:image"):
                    return base64.b64decode(url.split(",", 1)[1])

    return None


def _generate_gpt_image2(
    client: OpenAI,
    prompt: str,
) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """Text-to-image via POST /images/generations for gpt-image-2."""
    response = client.images.generate(
        model=GPT_IMAGE_2,
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="low",
    )
    b64 = response.data[0].b64_json
    if not b64:
        return False, None, "No b64_json in /images/generations response"
    return True, base64.b64decode(b64), None


def _edit_gpt_image2(
    client: OpenAI,
    prompt: str,
    reference_image_path: str,
) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """Image editing via POST /images/edits for gpt-image-2."""
    ref_path = Path(reference_image_path)
    if not ref_path.exists():
        return False, None, f"reference_image not found: {reference_image_path}"

    img_bytes = ref_path.read_bytes()
    # Detect MIME type from extension
    suffix = ref_path.suffix.lower()
    mime = (
        "image/png"
        if suffix == ".png"
        else "image/jpeg"
        if suffix in (".jpg", ".jpeg")
        else "image/png"
    )

    response = client.images.edit(
        model=GPT_IMAGE_2,
        image=(ref_path.name, img_bytes, mime),
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="low",
    )
    b64 = response.data[0].b64_json
    if not b64:
        return False, None, "No b64_json in /images/edits response"
    return True, base64.b64decode(b64), None


def generate_slide(
    client: OpenAI,
    slide: Dict,
    output_dir: Path,
    model: str,
    output_format: str,
    quality: int,
    global_temperature: Optional[float] = None,
    global_seed: Optional[int] = None,
    reference_image: Optional[str] = None,
) -> Tuple[bool, Optional[str], Optional[str], Optional[int], Optional[float]]:
    """Generate a single slide.

    Routes to gpt-image-2 endpoints or chat.completions based on model name.
    Returns:
        Tuple of (success, output_path, error_message, actual_seed, actual_temperature)
        seed and temperature are None for gpt-image-2 (not supported by API).
    """
    try:
        slide_num = slide["number"]
        prompt = slide["prompt"]
        output_path = output_dir / f"slide-{slide_num:02d}.{output_format}"

        # --- Shared: TrendLife layout detection ---
        layout_type = None
        is_trendlife_featured = False
        if slide.get("style") == "trendlife":
            explicit_layout = slide.get("layout")
            if explicit_layout == "featured":
                layout_type = "title"
                is_trendlife_featured = True
            elif explicit_layout == "content":
                layout_type = "content"
                is_trendlife_featured = False
            else:
                from logo_overlay import detect_layout_type

                layout_type = detect_layout_type(
                    slide["prompt"], slide_number=slide["number"]
                )
                is_trendlife_featured = layout_type == "title"

        # --- Shared: style prompt enhancement ---
        if "style" in slide:
            style = slide["style"]
            if style == "professional":
                prompt = f"Professional presentation slide: {prompt}. Clean, minimal design with clear typography."
            elif style == "data-viz":
                prompt = f"Data visualization slide: {prompt}. Clear charts and graphs, professional color scheme."
            elif style == "infographic":
                prompt = f"Infographic style: {prompt}. Visual storytelling with icons and illustrations."
            elif style == "trendlife":
                if is_trendlife_featured:
                    prompt = f"{prompt}\n\nThis is a title/cover slide for TrendLife (Trend Micro presentations).\nCreate a professional cover design that incorporates the TrendLife logo provided as reference image.\nUse TrendLife brand colors:\n- Trend Red (#D71920) for title and accents\n- Supporting colors: Guardian Red (#6F0000), Dark gray (#57585B), Medium gray (#808285), Light gray (#E7E6E6)\n- Black (#000000) for text, white (#FFFFFF) for backgrounds\nIMPORTANT: Use the exact logo from the reference image - DO NOT modify, redraw, or stylize the logo.\nPosition it prominently (typically center or upper area).\nKeep the design clean and professional."
                else:
                    prompt = f"{prompt}\n\nUse TrendLife brand colors for Trend Micro presentations:\n- IMPORTANT: Title text and all headings MUST be in Trend Red (#D71920)\n- Primary accents and highlights: Trend Red (#D71920)\n- Guardian Red (#6F0000) for supporting elements and depth\n- Neutral palette: Dark gray (#57585B), medium gray (#808285), light gray (#E7E6E6)\n- Black (#000000) for body text, white (#FFFFFF) for backgrounds\nKeep the design clean, professional, and suitable for corporate presentations.\nDO NOT include any logos or brand text - these will be added separately."

        use_lossless = output_format == "webp" and slide.get("style") in [
            "professional",
            "data-viz",
            "infographic",
            "trendlife",
        ]

        # --- gpt-image-2 routing ---
        if model == GPT_IMAGE_2:
            logo_path = (
                Path(__file__).parent.parent
                / "assets/logos/trendlife-2026-logo-light.png"
            )
            if slide.get("style") == "trendlife" and is_trendlife_featured:
                ok, image_bytes, err = _edit_gpt_image2(client, prompt, str(logo_path))
            elif reference_image:
                ok, image_bytes, err = _edit_gpt_image2(client, prompt, reference_image)
            else:
                ok, image_bytes, err = _generate_gpt_image2(client, prompt)

            if not ok:
                return False, None, err, None, None

            image = PILImage.open(io.BytesIO(image_bytes))
            _save_image(
                image, output_path, output_format, quality, lossless=use_lossless
            )

            if slide.get("style") == "trendlife" and not is_trendlife_featured:
                from logo_overlay import overlay_logo

                temp_output = output_path.with_stem(output_path.stem + "_with_logo")
                try:
                    overlay_logo(
                        background_path=output_path,
                        logo_path=logo_path,
                        output_path=temp_output,
                        layout_type=layout_type,
                    )
                    temp_output.replace(output_path)
                except Exception as e:
                    print(
                        f"Warning: Logo overlay failed for slide {slide['number']}: {e}",
                        file=sys.stderr,
                    )

            return True, str(output_path), None, None, None

        # --- Gemini / chat.completions routing ---
        temperature = slide.get(
            "temperature", global_temperature if global_temperature is not None else 1.0
        )

        seed = slide.get("seed")
        if seed is None:
            seed = global_seed
        if seed is None:
            seed = generate_seed()

        # Build messages
        if is_trendlife_featured:
            logo_path = (
                Path(__file__).parent.parent
                / "assets/logos/trendlife-2026-logo-light.png"
            )
            logo_b64 = _load_logo_base64(logo_path)
            if logo_b64 is None:
                return False, None, "Failed to load logo image", None, None

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{logo_b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
        else:
            messages = [{"role": "user", "content": prompt}]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            seed=seed,
            temperature=temperature,
            extra_body={"response_modalities": ["IMAGE"]},
        )

        image_bytes = _extract_image_bytes(response)
        if image_bytes is None:
            return False, None, "No image data in response", None, None

        image = PILImage.open(io.BytesIO(image_bytes))
        _save_image(image, output_path, output_format, quality, lossless=use_lossless)

        # TrendLife Logo Overlay
        if slide.get("style") == "trendlife":
            from logo_overlay import overlay_logo, detect_layout_type

            explicit_layout = slide.get("layout")
            should_overlay = True

            if explicit_layout == "featured":
                should_overlay = False
            elif explicit_layout == "content":
                should_overlay = True
            else:
                if layout_type is None:
                    layout_type = detect_layout_type(
                        slide["prompt"], slide_number=slide["number"]
                    )
                should_overlay = layout_type != "title"

            if should_overlay:
                logo_path = (
                    Path(__file__).parent.parent
                    / "assets/logos/trendlife-2026-logo-light.png"
                )
                temp_output = output_path.with_stem(output_path.stem + "_with_logo")
                try:
                    overlay_logo(
                        background_path=output_path,
                        logo_path=logo_path,
                        output_path=temp_output,
                        layout_type=layout_type,
                    )
                    temp_output.replace(output_path)
                except Exception as e:
                    print(
                        f"Warning: Logo overlay failed for slide {slide['number']}: {e}",
                        file=sys.stderr,
                    )

        return True, str(output_path), None, seed, temperature

    except Exception as e:
        return False, None, str(e), None, None


def _save_image(
    image: PILImage.Image,
    output_path: Path,
    output_format: str,
    quality: int,
    lossless: bool,
) -> None:
    if output_format == "webp":
        image.save(output_path, "WEBP", quality=quality, lossless=lossless)
    elif output_format == "png":
        image.save(output_path, "PNG", optimize=True)
    elif output_format in ["jpeg", "jpg"]:
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        image.save(output_path, "JPEG", quality=quality, optimize=True)
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def check_environment():
    if sys.version_info < (3, 9):
        print(
            f"Error: Python 3.9+ required, but running {sys.version_info.major}.{sys.version_info.minor}",
            file=sys.stderr,
        )
        sys.exit(1)
    elif sys.version_info < (3, 14):
        print(
            f"Warning: Python {sys.version_info.major}.{sys.version_info.minor} detected. Python 3.11-3.13 is recommended (3.14+ breaks pydantic-core).",
            file=sys.stderr,
        )


def main():
    check_environment()

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    if len(sys.argv) != 3 or sys.argv[1] != "--config":
        print(
            "Usage: uv run generate_images.py --config <config_file>", file=sys.stderr
        )
        sys.exit(1)

    config_path = sys.argv[2]
    config = load_config(config_path)

    slides = config["slides"]
    output_dir = Path(config["output_dir"])

    model = os.environ.get("IMAGE_GEN_MODEL") or "gemini-3-pro-image"
    output_format = config.get("format", "webp").lower()
    quality = config.get("quality", 90)
    global_temperature = config.get("temperature")
    global_seed = config.get("seed")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: Cannot create output directory: {e}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("RDSEC_API_KEY")
    if not api_key:
        print(
            "Error: RDSEC_API_KEY environment variable not set",
            file=sys.stderr,
        )
        sys.exit(1)

    base_url = os.environ.get("IMAGE_GEN_BASE_URL")
    if not base_url:
        print(
            "Error: IMAGE_GEN_BASE_URL environment variable not set",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        print(f"Error: Failed to initialize API client: {e}", file=sys.stderr)
        sys.exit(1)

    started_at = datetime.now(UTC).isoformat() + "Z"
    completed = []
    failed = []
    errors = []

    if model == GPT_IMAGE_2:
        has_global_seed = global_seed is not None
        has_slide_seed = any("seed" in s for s in slides)
        if has_global_seed or has_slide_seed:
            print(
                "Warning: seed is not supported for gpt-image-2, ignoring",
                file=sys.stderr,
            )
        has_global_temp = global_temperature is not None
        has_slide_temp = any("temperature" in s for s in slides)
        if has_global_temp or has_slide_temp:
            print(
                "Warning: temperature is not supported for gpt-image-2, ignoring",
                file=sys.stderr,
            )

    for i, slide in enumerate(slides):
        slide_num = slide["number"]
        status = f"generating slide {slide_num}..."

        write_progress(
            i, len(slides), status, [c["path"] for c in completed], failed, started_at
        )

        reference_image = slide.get("reference_image")
        success, output_path, error, actual_seed, actual_temp = generate_slide(
            client,
            slide,
            output_dir,
            model,
            output_format,
            quality,
            global_temperature,
            global_seed,
            reference_image=reference_image,
        )

        if success:
            size_kb = Path(output_path).stat().st_size // 1024
            slide_result = {"slide": slide_num, "path": output_path, "size_kb": size_kb}
            if actual_seed is not None:
                slide_result["seed"] = actual_seed
            if actual_temp is not None:
                slide_result["temperature"] = actual_temp
            completed.append(slide_result)
            print(f"✓ Slide {slide_num} completed: {output_path}")
        else:
            failed.append(slide_num)
            errors.append(
                {
                    "slide": slide_num,
                    "error": error or "Unknown error",
                    "timestamp": datetime.now(UTC).isoformat() + "Z",
                }
            )
            print(f"✗ Slide {slide_num} failed: {error}", file=sys.stderr)

    write_progress(
        len(slides),
        len(slides),
        "completed",
        [c["path"] for c in completed],
        failed,
        started_at,
    )

    write_results(completed, failed, errors, started_at)

    try:
        results_in_output = output_dir / "generation-results.json"
        started_dt = datetime.fromisoformat(started_at.rstrip("Z"))
        completed_at = datetime.now(UTC).isoformat() + "Z"
        completed_dt = datetime.fromisoformat(completed_at.rstrip("Z"))
        duration = (completed_dt - started_dt).total_seconds()

        results = {
            "completed": len(completed),
            "failed": len(failed),
            "total": len(completed) + len(failed),
            "outputs": completed,
            "errors": errors,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": int(duration),
        }

        with open(results_in_output, "w") as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        print(
            f"Warning: Failed to write results to output directory: {e}",
            file=sys.stderr,
        )

    print(f"\n{'=' * 60}")
    print("Batch generation completed")
    print(f"{'=' * 60}")
    print(f"Completed: {len(completed)}/{len(slides)}")
    print(f"Failed: {len(failed)}/{len(slides)}")
    if completed:
        print(f"\nOutput directory: {output_dir}")
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  Slide {err['slide']}: {err['error']}")

    try:
        PROGRESS_FILE.unlink(missing_ok=True)
        RESULTS_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    sys.exit(0 if completed else 1)


if __name__ == "__main__":
    main()
