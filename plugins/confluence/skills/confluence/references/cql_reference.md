# CQL (Confluence Query Language) Reference

## Basic Syntax

```
field operator value [AND|OR] field operator value
```

## Common Fields

| Field | Description | Example |
|-------|-------------|---------|
| `space` | Space key | `space = "DEV"` |
| `title` | Page title | `title ~ "API"` |
| `text` | Page content | `text ~ "authentication"` |
| `type` | Content type | `type = page` |
| `creator` | Created by | `creator = "john@example.com"` |
| `contributor` | Modified by | `contributor = currentUser()` |
| `created` | Creation date | `created >= 2024-01-01` |
| `lastmodified` | Last modified | `lastmodified >= startOfMonth()` |
| `label` | Page labels | `label = "documentation"` |
| `parent` | Parent page | `parent = "123456"` |
| `ancestor` | Any ancestor | `ancestor = "123456"` |

## Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `space = "DEV"` |
| `!=` | Not equals | `type != blogpost` |
| `~` | Contains (fuzzy) | `title ~ "API"` |
| `!~` | Not contains | `text !~ "deprecated"` |
| `>`, `>=` | Greater than | `created >= 2024-01-01` |
| `<`, `<=` | Less than | `lastmodified < endOfDay()` |
| `IN` | In list | `space IN ("DEV", "PROD")` |
| `NOT IN` | Not in list | `label NOT IN ("draft", "archived")` |

## Date Functions

| Function | Description |
|----------|-------------|
| `now()` | Current timestamp |
| `startOfDay()` | Start of today |
| `endOfDay()` | End of today |
| `startOfWeek()` | Start of current week |
| `endOfWeek()` | End of current week |
| `startOfMonth()` | Start of current month |
| `endOfMonth()` | End of current month |
| `startOfYear()` | Start of current year |
| `endOfYear()` | End of current year |

**With offset:**

```
startOfDay(-7)     -- 7 days ago
startOfMonth(-1)   -- Start of last month
startOfYear(1)     -- Start of next year
```

## User Functions

| Function | Description |
|----------|-------------|
| `currentUser()` | Current logged-in user |

## Content Types

- `page` - Regular pages
- `blogpost` - Blog posts
- `comment` - Comments
- `attachment` - Attachments

## Example Queries

**Pages in a space:**

```cql
space = "DEV" AND type = page
```

**Pages containing text:**

```cql
space = "DEV" AND text ~ "authentication"
```

**Pages modified this week:**

```cql
lastmodified >= startOfWeek()
```

**Pages I created:**

```cql
creator = currentUser()
```

**Pages with specific label:**

```cql
label = "api-docs" AND space = "DEV"
```

**Pages under a parent:**

```cql
ancestor = "123456789"
```

**Recent pages by multiple contributors:**

```cql
contributor IN ("alice@example.com", "bob@example.com")
AND created >= startOfMonth(-1)
```

**Excluding drafts:**

```cql
space = "DEV" AND label != "draft"
```

**Complex search:**

```cql
space IN ("DEV", "PROD")
AND type = page
AND (title ~ "API" OR label = "api-docs")
AND created >= startOfYear()
ORDER BY lastmodified DESC
```

## Sorting

```cql
... ORDER BY created DESC
... ORDER BY title ASC
... ORDER BY lastmodified DESC
```

## MCP Usage

```javascript
mcp__atlassian__confluence_search({
  query: 'space = "DEV" AND text ~ "API" AND created >= startOfYear()',
  limit: 20
})
```
