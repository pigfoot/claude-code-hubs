#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pymupdf",
#   "requests",
# ]
# ///

"""
Taiwan MRT Far Eastern Hospital Empty Train Finder

Identifies trains that originate at 亞東醫院 station (空車) vs those arriving
from 海山 station. Empty trains are less crowded.

Usage:
    uv run --managed-python scripts/mrt_empty_train.py query [options]
    uv run --managed-python scripts/mrt_empty_train.py all [options]
    uv run --managed-python scripts/mrt_empty_train.py refresh
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import fitz  # pymupdf
import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TAIWAN_TZ = ZoneInfo("Asia/Taipei")
CACHE_DIR = Path.home() / ".cache" / "taiwan-mrt"
MANIFEST_FILE = CACHE_DIR / "manifest.json"
CACHE_MAX_AGE_DAYS = 7

# TRTC official timetable PDFs
PDF_URLS = {
    "far_eastern_hospital": "https://web.metro.taipei/img/ALL/timetables/080a.PDF",
    "haishan": "https://web.metro.taipei/img/ALL/timetables/079a.PDF",
}
PDF_FILES = {
    "far_eastern_hospital": CACHE_DIR / "080a.PDF",
    "haishan": CACHE_DIR / "079a.PDF",
}

# Default travel time 海山 → 亞東醫院 (minutes)
DEFAULT_TRAVEL_TIME = 3

# Column definitions based on PDF x-coordinate analysis
# Format: (x_min, x_max, day_type_key, hour_zone_width)
#   x_min/x_max: column boundaries
#   hour_zone_width: spans within x_min..(x_min + hour_zone_width) are hour markers
COLUMN_DEFS = [
    (21, 155, "mon_thu", 20),
    (160, 295, "friday", 20),
    (300, 435, "saturday", 20),
    (439, 569, "sunday_holiday", 20),
]

DAY_TYPE_NAMES = {
    "mon_thu": "平常日(週一至週四)",
    "friday": "平常日(週五)",
    "saturday": "週六",
    "sunday_holiday": "週日及國定假日",
}

# ---------------------------------------------------------------------------
# PDF download & caching
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_pdf(url: str, dest: Path) -> str:
    """Download PDF to dest; return SHA256 checksum."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(
        url,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return sha256_file(dest)


# ---------------------------------------------------------------------------
# PDF parsing
# ---------------------------------------------------------------------------


def get_column(x: float) -> Optional[tuple[str, float]]:
    """Return (day_type, hour_zone_x_max) for x-coordinate, or None."""
    for x_min, x_max, day_type, hour_w in COLUMN_DEFS:
        if x_min <= x < x_max:
            return day_type, x_min + hour_w
    return None


def parse_timetable_pdf(pdf_path: Path) -> tuple[dict, str]:
    """
    Parse a TRTC station timetable PDF.

    Returns:
        timetable: dict keyed by day_type → hour_str → sorted list of minutes
        effective_date: string like "114.11.10" from PDF footer
    """
    doc = fitz.open(str(pdf_path))

    timetable: dict[str, dict[str, list[int]]] = {d: {} for _, _, d, _ in COLUMN_DEFS}
    effective_date = ""
    current_hour: dict[str, Optional[str]] = {d: None for _, _, d, _ in COLUMN_DEFS}

    for page in doc:
        # Collect all text spans with (y, x, text), sorted top-to-bottom then left-to-right
        spans: list[tuple[float, float, str]] = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        spans.append((span["bbox"][1], span["bbox"][0], text))
        spans.sort()

        for _y, x, text in spans:
            # Extract effective date from footer (e.g. "114.11.10生效")
            m = re.search(r"(\d{3}\.\d{1,2}\.\d{1,2})生效", text)
            if m:
                effective_date = m.group(1)
                continue

            col_info = get_column(x)
            if col_info is None:
                continue
            day_type, hour_zone_x_max = col_info

            nums = re.findall(r"\d+", text)
            if not nums:
                continue

            if x < hour_zone_x_max:
                # Hour zone: first number in range 4–24 becomes current hour
                for num_str in nums:
                    n = int(num_str)
                    if 4 <= n <= 24:
                        current_hour[day_type] = f"{n:02d}"
                        timetable[day_type].setdefault(current_hour[day_type], [])
                        break
            else:
                # Minute zone: all numbers 0–59 are minutes under current hour
                if current_hour[day_type] is None:
                    continue
                hour_key = current_hour[day_type]
                minute_list = timetable[day_type][hour_key]
                for num_str in nums:
                    n = int(num_str)
                    if 0 <= n <= 59 and n not in minute_list:
                        minute_list.append(n)

    # Sort all minute lists
    for day_type in timetable:
        for hour in timetable[day_type]:
            timetable[day_type][hour].sort()

    doc.close()
    return timetable, effective_date


# ---------------------------------------------------------------------------
# Manifest (cache)
# ---------------------------------------------------------------------------


def load_or_refresh_manifest(force: bool = False) -> dict:
    """Load manifest from cache, refreshing if stale or forced."""
    if not force and MANIFEST_FILE.exists():
        try:
            manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
            generated_at = datetime.fromisoformat(manifest["generated_at"])
            age = datetime.now() - generated_at
            if age < timedelta(days=CACHE_MAX_AGE_DAYS):
                return manifest
            print(
                f"Cache is {age.days} days old (>{CACHE_MAX_AGE_DAYS}), refreshing...",
                file=sys.stderr,
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            print("Cache corrupted, refreshing...", file=sys.stderr)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    checksums: dict[str, str] = {}
    stations_data: dict[str, dict] = {}
    effective_date = ""

    for station_key in ["far_eastern_hospital", "haishan"]:
        url = PDF_URLS[station_key]
        pdf_path = PDF_FILES[station_key]
        pdf_id = pdf_path.stem.lower()

        print(f"Downloading {url}...", file=sys.stderr)
        checksums[pdf_id] = download_pdf(url, pdf_path)

        print(f"Parsing {pdf_path.name}...", file=sys.stderr)
        timetable, eff = parse_timetable_pdf(pdf_path)
        stations_data[station_key] = timetable
        if eff:
            effective_date = eff

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "effective_date": effective_date,
        "pdf_checksums": checksums,
        "stations": stations_data,
    }
    MANIFEST_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Manifest saved: {MANIFEST_FILE}", file=sys.stderr)
    if effective_date:
        print(f"Timetable effective date: {effective_date}", file=sys.stderr)

    return manifest


# ---------------------------------------------------------------------------
# Day type
# ---------------------------------------------------------------------------


def get_day_type_fallback(date: datetime) -> str:
    """Weekday-based day type detection (no holiday awareness)."""
    w = date.weekday()  # 0=Mon, 6=Sun
    if w <= 3:
        return "mon_thu"
    elif w == 4:
        return "friday"
    elif w == 5:
        return "saturday"
    else:
        return "sunday_holiday"


def resolve_day_type(args: argparse.Namespace) -> str:
    """Determine day type from CLI args."""
    if getattr(args, "day_type", None):
        return args.day_type
    if getattr(args, "holiday", False):
        return "sunday_holiday"
    date_str = getattr(args, "date", None)
    if date_str:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date = datetime.now(TAIWAN_TZ)
    return get_day_type_fallback(date)


# ---------------------------------------------------------------------------
# Train logic
# ---------------------------------------------------------------------------


def get_all_departures(timetable: dict, day_type: str) -> list[tuple[int, int]]:
    """Return sorted (hour, minute) departure list for a day type."""
    result: list[tuple[int, int]] = []
    for hour_str, minutes in timetable.get(day_type, {}).items():
        h = int(hour_str)
        for m in minutes:
            result.append((h, m))
    return sorted(result)


def find_empty_trains(
    manifest: dict,
    day_type: str,
    travel_time: int = DEFAULT_TRAVEL_TIME,
) -> list[tuple[tuple[int, int], bool]]:
    """
    Return list of (dep_time, is_empty) for all 亞東醫院 departures.
    is_empty=True  → train originates at 亞東醫院 (空車)
    is_empty=False → train came from 海山 (海山發)
    """
    feh_times = get_all_departures(
        manifest["stations"]["far_eastern_hospital"], day_type
    )
    hs_times = get_all_departures(manifest["stations"]["haishan"], day_type)

    # 海山 departure + travel_time (or +1 min tolerance) = expected arrival at 亞東醫院
    hs_arrivals: set[tuple[int, int]] = set()
    for h, m in hs_times:
        for tt in (travel_time, travel_time + 1):
            total = h * 60 + m + tt
            hs_arrivals.add((total // 60, total % 60))

    return [(dep, dep not in hs_arrivals) for dep in feh_times]


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def fmt_time(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def parse_query_time(args: argparse.Namespace) -> tuple[int, int]:
    if getattr(args, "time", None):
        t = datetime.strptime(args.time, "%H:%M")
        return t.hour, t.minute
    now = datetime.now(TAIWAN_TZ)
    return now.hour, now.minute


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def cmd_query(args: argparse.Namespace, manifest: dict) -> None:
    """Show next N empty trains (空車 only)."""
    qh, qm = parse_query_time(args)
    day_type = resolve_day_type(args)
    q_total = qh * 60 + qm

    trains = find_empty_trains(manifest, day_type, args.travel_time)
    empty = [
        dep
        for dep, is_empty in trains
        if is_empty and (dep[0] * 60 + dep[1]) >= q_total
    ]

    print(f"亞東醫院 空車班次 ({DAY_TYPE_NAMES[day_type]})，{fmt_time(qh, qm)} 之後：")
    if not empty:
        print("  今日空車班次已結束")
        return
    for dep in empty[: args.count]:
        print(f"  {fmt_time(*dep)} 空車")


def cmd_all(args: argparse.Namespace, manifest: dict) -> None:
    """Show all trains after query time with 空車/海山發 labels."""
    qh, qm = parse_query_time(args)
    day_type = resolve_day_type(args)
    q_total = qh * 60 + qm

    trains = find_empty_trains(manifest, day_type, args.travel_time)
    after = [
        (dep, is_empty) for dep, is_empty in trains if (dep[0] * 60 + dep[1]) >= q_total
    ]

    count = getattr(args, "count", None)
    display = after[:count] if count else after

    print(f"亞東醫院 班次列表 ({DAY_TYPE_NAMES[day_type]})，{fmt_time(qh, qm)} 之後：")
    if not display:
        print("  今日班次已結束")
        return
    for dep, is_empty in display:
        label = "空車" if is_empty else "海山發"
        print(f"  {fmt_time(*dep)} {label}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--time", "-t", metavar="HH:MM", help="Query time (default: now)")
    p.add_argument(
        "--date", "-d", metavar="YYYY-MM-DD", help="Query date (default: today)"
    )
    p.add_argument(
        "--day-type",
        choices=["mon_thu", "friday", "saturday", "sunday_holiday"],
        help="Override day type (pass result from taiwan-calendar skill)",
    )
    p.add_argument(
        "--holiday",
        action="store_true",
        help="Force Sunday/Holiday timetable",
    )
    p.add_argument(
        "--travel-time",
        type=int,
        default=DEFAULT_TRAVEL_TIME,
        metavar="MIN",
        help=f"海山→亞東醫院 travel time in minutes (default: {DEFAULT_TRAVEL_TIME})",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Taiwan MRT Far Eastern Hospital Empty Train Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Next 5 empty trains (using taiwan-calendar day type)
  uv run --managed-python scripts/mrt_empty_train.py query --day-type mon_thu

  # All trains from 08:00, Sunday timetable
  uv run --managed-python scripts/mrt_empty_train.py all --day-type sunday_holiday --time 08:00

  # Force refresh timetable cache
  uv run --managed-python scripts/mrt_empty_train.py refresh
""",
    )
    sub = parser.add_subparsers(dest="command")

    p_query = sub.add_parser("query", help="Show next N empty trains (空車 only)")
    add_common_args(p_query)
    p_query.add_argument(
        "--count",
        "-n",
        type=int,
        default=5,
        metavar="N",
        help="Number of trains to show (default: 5)",
    )

    p_all = sub.add_parser("all", help="Show all trains with 空車/海山發 labels")
    add_common_args(p_all)
    p_all.add_argument(
        "--count",
        "-n",
        type=int,
        default=None,
        metavar="N",
        help="Max trains to show (default: all)",
    )

    sub.add_parser("refresh", help="Force re-download PDFs and regenerate cache")

    args = parser.parse_args()

    if args.command == "refresh":
        load_or_refresh_manifest(force=True)
        print("Done.")
        return

    if args.command is None:
        parser.print_help()
        return

    manifest = load_or_refresh_manifest()

    if args.command == "query":
        cmd_query(args, manifest)
    elif args.command == "all":
        cmd_all(args, manifest)


if __name__ == "__main__":
    main()
