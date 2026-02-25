---
name: taiwan-mrt-fareastern-empty-train
description: Find empty trains (空車) at 亞東醫院 MRT station. Use when user asks about empty trains, 空車, or uncrowded trains at 亞東醫院/Far Eastern Hospital station on the Bannan line.
allowed-tools: Bash
metadata:
  short-description: Find empty/uncrowded trains at 亞東醫院 MRT station
  version: "0.0.1"
license: MIT
---

# Taiwan MRT Far Eastern Hospital Empty Train Finder

Identifies trains that originate at 亞東醫院 station (空車) vs those arriving from
海山 station. Empty trains are less crowded because no passengers have boarded yet.

## Background

The Bannan line (板南線) terminates at 頂埔 on the west end. Trains departing from
亞東醫院 are "empty trains" (空車) — they originate here with no passengers.
Trains coming from 海山 (3 minutes west) already have riders.

Travel time: 海山 → 亞東醫院 ≈ 3 minutes

---

## When to Use

**Trigger when user asks about:**

- 亞東醫院 空車 / empty trains at Far Eastern Hospital station
- 捷運空車 / which trains are less crowded
- 幾點有空車 / when are the empty trains
- 下一班空車 / next empty train

---

## Workflow

### Step 1: Determine Day Type

**Always determine the correct day type BEFORE running the script.**

Use the `taiwan-calendar` skill to check if the query date is a holiday or working day.
Run `taiwan_calendar.py check <YYYY-MM-DD>` from within the taiwan-calendar skill directory.

Map the result to a `--day-type` value:

| taiwan-calendar output | Weekday | `--day-type` |
|------------------------|---------|--------------|
| 非工作日 (國定假日 or Sunday) | any | `sunday_holiday` |
| 非工作日 (Saturday, not 補班) | Sat | `saturday` |
| 工作日 (including 補班 on Saturday) | Mon–Thu | `mon_thu` |
| 工作日 | Friday | `friday` |

> **If taiwan-calendar skill is unavailable:** Omit `--day-type` entirely. The script
> falls back to weekday-based detection (no holiday awareness).

### Step 2: Run the Script

From **this skill's directory** (`skills/taiwan-mrt-fareastern-empty-train/`):

```bash
# Show next N empty trains (空車 only)
uv run --managed-python scripts/mrt_empty_train.py query \
  --day-type <type> \
  --time HH:MM \
  --count 5

# Show all trains with 空車/海山發 labels
uv run --managed-python scripts/mrt_empty_train.py all \
  --day-type <type> \
  --time HH:MM \
  --count 10
```

---

## Commands

### `query` — Next Empty Trains

Shows the next N trains that originate at 亞東醫院 (空車 only).

```bash
uv run --managed-python scripts/mrt_empty_train.py query \
  --day-type mon_thu \
  --time 08:30 \
  --count 5
```

**Output:**

```
亞東醫院 空車班次 (平常日(週一至週四))，08:30 之後：
  08:30 空車
  08:34 空車
  08:37 空車
  08:44 空車
  08:50 空車
```

### `all` — All Trains with Labels

Shows all trains after the query time, labelled 空車 or 海山發.

```bash
uv run --managed-python scripts/mrt_empty_train.py all \
  --day-type mon_thu \
  --time 06:00 \
  --count 7
```

**Output:**

```
亞東醫院 班次列表 (平常日(週一至週四))，06:00 之後：
  06:00 空車
  06:05 空車
  06:10 海山發
  06:17 海山發
  06:21 空車
  06:25 海山發
  06:30 海山發
```

### `refresh` — Force Re-download

Downloads latest PDFs from TRTC and regenerates cache.

```bash
uv run --managed-python scripts/mrt_empty_train.py refresh
```

---

## Parameters

| Parameter | Description |
|-----------|-------------|
| `--time HH:MM` | Query time (default: current time) |
| `--date YYYY-MM-DD` | Query date for fallback weekday detection (default: today) |
| `--day-type TYPE` | Day type: `mon_thu`, `friday`, `saturday`, `sunday_holiday` |
| `--holiday` | Force Sunday/Holiday timetable |
| `--count N` | Max results to show |
| `--travel-time MIN` | 海山→亞東醫院 travel time in minutes (default: 3) |

---

## Cache

- Location: `~/.cache/taiwan-mrt/`
- Valid for: 7 days (auto-refreshes when stale)
- Force refresh: `refresh` command

---

## Full Example

```
User: 現在幾點有空車？

Step 1 — Get day type via taiwan-calendar:
  uv run --managed-python scripts/taiwan_calendar.py check 2026-02-25
  → "2026-02-25 (週三) 是工作日。"
  → day type = mon_thu

Step 2 — Query empty trains:
  uv run --managed-python scripts/mrt_empty_train.py query --day-type mon_thu
```

---

## Troubleshooting

### PDF download fails

- Check network connectivity
- TRTC may have updated PDF URLs; check <https://web.metro.taipei>
- URLs in script: `https://web.metro.taipei/img/ALL/timetables/080a.PDF`

### Empty output

- Try `refresh` to re-download the latest timetable
- Verify `--day-type` matches the actual date

### Unexpected results

- Run `refresh` to re-parse the latest PDFs
- Column x-coordinates may need adjustment if TRTC updated PDF layout
  (see `COLUMN_DEFS` constant in `scripts/mrt_empty_train.py`)
