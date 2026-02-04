## ADDED Requirements

### Requirement: Today's date and working day status

The system SHALL provide current Taiwan date (UTC+8) with weekday and working day status.

#### Scenario: Query today's information

- **WHEN** user runs `taiwan_calendar.py today`
- **THEN** system outputs today's date, weekday name, and whether it is a working day

#### Scenario: Today is a holiday

- **WHEN** today is a national holiday
- **THEN** output includes the holiday name (e.g., "National Day")

#### Scenario: Today is a make-up workday

- **WHEN** today is a make-up workday (補班日)
- **THEN** output indicates it is a working day with make-up workday note

### Requirement: Check specific date

The system SHALL allow checking any date for working day status and holiday information.

#### Scenario: Check a regular working day

- **WHEN** user runs `taiwan_calendar.py check 2025-01-06`
- **THEN** system outputs that date with weekday and "working day" status

#### Scenario: Check a holiday

- **WHEN** user runs `taiwan_calendar.py check 2025-01-01`
- **THEN** system outputs that date with weekday, "holiday" status, and holiday name "New Year's Day"

#### Scenario: Check a weekend

- **WHEN** user runs `taiwan_calendar.py check 2025-01-04`
- **THEN** system outputs that date as Saturday, non-working day

#### Scenario: Flexible date format input

- **WHEN** user provides date in various formats (YYYY-MM-DD, YYYY/MM/DD, MM/DD)
- **THEN** system parses and processes correctly

### Requirement: Count working days in range

The system SHALL calculate the number of working days between two dates.

#### Scenario: Count working days in a month

- **WHEN** user runs `taiwan_calendar.py range 2025-01-01 2025-01-31`
- **THEN** system outputs total working days count and lists holidays in that range

#### Scenario: Range spans multiple months

- **WHEN** date range spans February and March
- **THEN** system correctly handles month boundaries and leap years

### Requirement: Calculate N working days from date

The system SHALL calculate the date that is N working days from a given date.

#### Scenario: Add working days from today

- **WHEN** user runs `taiwan_calendar.py add-days 5`
- **THEN** system outputs the date 5 working days from today

#### Scenario: Add working days from specific date

- **WHEN** user runs `taiwan_calendar.py add-days 2025-01-06 5`
- **THEN** system outputs the date 5 working days from 2025-01-06

#### Scenario: Skip holidays in calculation

- **WHEN** calculation crosses a holiday period (e.g., Lunar New Year)
- **THEN** holidays are excluded from working day count

### Requirement: Find next working day

The system SHALL find the next working day from a given date.

#### Scenario: Next working day from today

- **WHEN** user runs `taiwan_calendar.py next-working`
- **THEN** system outputs the next working day after today

#### Scenario: Next working day from Friday

- **WHEN** user runs `taiwan_calendar.py next-working 2025-01-03` (Friday)
- **THEN** system outputs Monday 2025-01-06

#### Scenario: Next working day before long holiday

- **WHEN** query is made before Lunar New Year
- **THEN** system correctly identifies the first working day after the holiday

### Requirement: Find next holiday

The system SHALL find the next holiday from a given date.

#### Scenario: Next holiday from today

- **WHEN** user runs `taiwan_calendar.py next-holiday`
- **THEN** system outputs the next holiday date and name

#### Scenario: Multiple consecutive holidays

- **WHEN** next holiday is part of a multi-day holiday (e.g., Lunar New Year)
- **THEN** system shows the full holiday period

### Requirement: Local cache with 1-hour expiry

The system SHALL cache calendar data locally for 1 hour to reduce API calls.

#### Scenario: First query fetches from API

- **WHEN** no cache exists or cache is expired
- **THEN** system fetches from government API and creates cache

#### Scenario: Subsequent queries use cache

- **WHEN** cache exists and is less than 1 hour old
- **THEN** system uses cached data without API call

#### Scenario: Cache location is cross-platform

- **WHEN** running on different operating systems
- **THEN** cache file is stored in appropriate temp directory (via `tempfile.gettempdir()`)

### Requirement: Error handling for API failures

The system SHALL gracefully handle API failures with fallback and clear error messages.

#### Scenario: Primary API fails

- **WHEN** data.gov.tw API is unavailable
- **THEN** system attempts fallback API source

#### Scenario: All APIs fail

- **WHEN** all API sources are unavailable
- **THEN** system outputs clear error message explaining the issue

#### Scenario: Network unavailable

- **WHEN** no network connection
- **THEN** system attempts to use existing cache (even if expired) with warning
