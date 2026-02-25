# Taiwan MRT Far Eastern Hospital Empty Train Plugin

Find empty trains (空車) at 亞東醫院 (Far Eastern Hospital) MRT station on the Bannan line.

## What is an Empty Train (空車)?

Some trains on the Bannan line originate at 亞東醫院 station — they start their journey here with zero passengers.
These are called 空車 (empty trains). Trains coming from 海山 (one station west, ~3 minutes away) already have riders.

Catching an empty train means guaranteed seating and less crowding.

## How It Works

1. Parses TRTC official timetables for 亞東醫院 (080a.PDF) and 海山 (079a.PDF)
2. For each 亞東醫院 departure, checks if a 海山 departure + 3 minutes matches
3. If match → 海山發 (train came from 海山)
4. If no match → 空車 (train originates at 亞東醫院)

## Installation

### From Local Plugin

```bash
claude plugin install ./plugins/taiwan-mrt-fareastern-empty-train
```

### From Marketplace (if published)

```bash
claude plugin install taiwan-mrt-fareastern-empty-train@pigfoot-marketplace
```

## Usage

Once installed, Claude will automatically use this skill when you ask about empty trains:

```
You: "現在有空車嗎？"
Claude: [Uses taiwan-mrt-fareastern-empty-train skill]
       "亞東醫院 空車班次 (平常日(週一至週四))，09:15 之後：
         09:16 空車
         09:23 空車
         09:29 空車
         09:36 空車
         09:41 空車"

You: "週六早上八點空車怎麼排？"
Claude: [Uses taiwan-mrt-fareastern-empty-train skill]
       "亞東醫院 班次列表 (週六)，08:00 之後：
         08:00 空車
         08:04 空車
         08:09 海山發
         ..."
```

## Features

- **空車 detection**: Identifies trains originating at 亞東醫院 vs arriving from 海山
- **All day types**: Mon-Thu, Friday, Saturday, Sunday/Holiday timetables
- **Holiday awareness**: Works with `taiwan-calendar` plugin for accurate holiday detection
- **Automatic caching**: 7-day local cache, auto-refreshes when stale
- **Manual refresh**: Force re-download when TRTC updates timetables

## Commands Reference

All commands run from `skills/taiwan-mrt-fareastern-empty-train/`:

```bash
# Next 5 empty trains from now
uv run --managed-python scripts/mrt_empty_train.py query --day-type mon_thu

# Next empty trains from specific time
uv run --managed-python scripts/mrt_empty_train.py query --day-type mon_thu --time 08:30 --count 5

# All trains with 空車/海山發 labels
uv run --managed-python scripts/mrt_empty_train.py all --day-type saturday --time 09:00

# Force re-download timetable PDFs
uv run --managed-python scripts/mrt_empty_train.py refresh
```

### Day Types

| `--day-type` | Applies to |
|---|---|
| `mon_thu` | Monday to Thursday (平常日) |
| `friday` | Friday (平常日週五) |
| `saturday` | Saturday (週六) |
| `sunday_holiday` | Sunday and national holidays (週日及國定假日) |

## Requirements

- Python 3.11+ (automatically managed by `uv`)
- Internet connection (for initial PDF download)
- Dependencies (automatically installed):
  - `pymupdf`
  - `requests`

## Technical Details

- **Data source**: TRTC official timetable PDFs (`web.metro.taipei`)
- **Stations**: 亞東醫院 (080a.PDF), 海山 (079a.PDF)
- **Travel time**: 海山 → 亞東醫院 ≈ 3 minutes (configurable via `--travel-time`)
- **Cache location**: `~/.cache/taiwan-mrt/`
- **Cache expiry**: 7 days

## Troubleshooting

### PDF download fails

- Check network connectivity
- TRTC may have updated PDF URLs; check `https://web.metro.taipei`

### Empty or missing trains

- Run `refresh` to re-download the latest timetable
- Verify `--day-type` matches the actual date

### Holiday detection

If results seem wrong for holidays, ensure the `taiwan-calendar` plugin is installed — it provides accurate
holiday/working day classification. Without it, the script falls back to weekday-based detection (no holiday awareness).

## ✨ Recent Improvements (v0.0.1)

- Initial release
- PDF timetable parsing from TRTC official website
- Automatic 7-day cache with manual refresh
- Support for all day types: Mon-Thu, Friday, Saturday, Sunday/Holiday
- SKILL.md instructs AI to use taiwan-calendar skill for holiday detection (no hardcoded paths)

## License

MIT

## Author

pigfoot <pigfoot@gmail.com>

## Version

0.0.1
