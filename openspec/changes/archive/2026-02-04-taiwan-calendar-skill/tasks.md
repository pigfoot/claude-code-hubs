## 1. Plugin Structure Setup

- [x] 1.1 Create plugin directory structure: `plugins/taiwan-calendar/.claude-plugin/`
- [x] 1.2 Create `plugin.json` with metadata (name, description, version, author, skills)
- [x] 1.3 Create skill directory: `plugins/taiwan-calendar/skills/taiwan-calendar/`
- [x] 1.4 Create `scripts/` directory for Python script

## 2. Python Script - Core Infrastructure

- [x] 2.1 Create `taiwan_calendar.py` with PEP 723 inline metadata (dependencies: requests, python-dateutil)
- [x] 2.2 Implement CLI argument parsing with subcommands (today, check, range, add-days, next-working, next-holiday)
- [x] 2.3 Implement Taiwan timezone handling (UTC+8)
- [x] 2.4 Implement cross-platform cache file path using `tempfile.gettempdir()`
- [x] 2.5 Implement 1-hour cache expiry logic

## 3. Python Script - API Integration

- [x] 3.1 Implement government API fetcher (data.gov.tw administrative calendar)
- [x] 3.2 Implement fallback API source (New Taipei City open data)
- [x] 3.3 Parse API response to extract date, holiday name, working day status
- [x] 3.4 Handle API errors with clear error messages
- [x] 3.5 Handle network unavailable scenario (use expired cache with warning)

## 4. Python Script - Date Query Features

- [x] 4.1 Implement `today` command - show today's date, weekday, working day status
- [x] 4.2 Implement `check <date>` command - query specific date
- [x] 4.3 Implement flexible date format parsing (YYYY-MM-DD, YYYY/MM/DD, MM/DD)
- [x] 4.4 Implement `range <start> <end>` command - count working days in range

## 5. Python Script - Advanced Features

- [x] 5.1 Implement `add-days [date] <n>` command - calculate N working days later
- [x] 5.2 Implement `next-working [date]` command - find next working day
- [x] 5.3 Implement `next-holiday [date]` command - find next holiday
- [x] 5.4 Handle cross-year date calculations

## 6. SKILL.md Creation

- [x] 6.1 Create SKILL.md with frontmatter (name, description, allowed-tools, version)
- [x] 6.2 Write trigger conditions section (when Claude should use this skill)
- [x] 6.3 Document CLI commands with examples
- [x] 6.4 Add usage examples for common scenarios

## 7. Documentation and Registry Updates

- [x] 7.1 Create plugin README.md with installation and usage instructions
- [x] 7.2 Add entry to `.claude-plugin/marketplace.json` (plugins registry)
- [x] 7.3 Update "Available Plugins" table in root `README.md` (~line 728)

## 8. Testing and Verification

- [x] 8.1 Test all CLI commands manually on local machine
- [x] 8.2 Verify cross-platform cache path works (macOS/Linux at minimum)
- [x] 8.3 Test API fallback when primary source fails
- [x] 8.4 Verify skill triggers correctly in Claude Code
