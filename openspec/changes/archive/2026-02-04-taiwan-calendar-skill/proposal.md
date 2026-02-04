## Why

Claude Code frequently makes errors with date-related queries due to knowledge cutoff limitations—getting weekdays
wrong, not knowing Taiwan's national holidays, and being unaware of make-up workdays. Users need to repeatedly
correct Claude's responses, leading to poor experience. A skill is needed to enable Claude to query Taiwan government
calendar API in real-time for accurate working day/holiday information.

## What Changes

- Add `taiwan-calendar` plugin with a skill of the same name
- Provide Python script (`taiwan_calendar.py`) that fetches government open data platform's administrative calendar
- Supported features:
  - Today's date + weekday + working day status
  - Specific date query (working day/holiday + reason)
  - Working day count for date range
  - Calculate date N working days from a given date
  - Next working day/holiday lookup
- Execute with `uv run --managed-python`, no Python pre-installation required
- Micro local cache (1-hour expiry) using `tempfile.gettempdir()` for cross-platform support

## Capabilities

### New Capabilities

- `taiwan-calendar`: Taiwan calendar query functionality including working day determination, holiday information,
  range calculations, and advanced date operations

### Modified Capabilities

<!-- None -->

## Impact

- Add `plugins/taiwan-calendar/` directory structure
- New Python script dependencies: `requests`, `python-dateutil`
- Creates cache file `taiwan-calendar-cache.json` in system temp directory
- Requires network connection to access government open data platform API
