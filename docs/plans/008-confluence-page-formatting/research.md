# Confluence Page Formatting Research

## Problem Statement

Pages created via `upload_confluence.py` use narrow (fixed-width) layout
by default, and tables have no column width control. The goal is to match
the formatting quality of manually-created pages like the AI Community
page (page ID 2299462199).

## Research Date

2026-03-24

---

## Finding 1: Page Width Control

### How Confluence Controls Page Width

Page width is NOT part of ADF or storage format content. It is controlled
via **content properties** on the page:

| Property Key | Values | Purpose |
|---|---|---|
| `content-appearance-published` | `full-width`, `fixed-width` | Published view |
| `content-appearance-draft` | `full-width`, `fixed-width` | Editor view |

### New Width Options (February 2026)

Confluence renamed width options and added a third:

| Display Name | API Value | Notes |
|---|---|---|
| Narrow | `fixed-width` | Default, ~760px content area |
| Wide | `full-width` | Wider, existing API value |
| Max | TBD | New option, API value not yet confirmed |

Source: [Compact Mode & Max Width announcement](https://community.atlassian.com/forums/Confluence-articles/New-feature-Compact-Mode-and-Max-Width-to-support-information/ba-p/3190468)

### Compact Mode

"Compact Mode" (smaller font, tighter line spacing) is a **frontend UI
preference only**. There is NO API to set it.

Source: [Developer community confirmation](https://community.developer.atlassian.com/t/how-to-set-compact-density-of-page-in-confluence-cloud-using-rest-api/97631)

### API Methods

**v1 API (atlassian-python-api):**

`create_page()` and `update_page()` both accept `full_width=True`.
Internally sets metadata properties in the request body.

```python
confluence.create_page(
    space=space_key, title=title, body=html,
    full_width=True  # <-- this is all we need
)
```

**v2 API (separate call required):**

```
POST /wiki/api/v2/pages/{page-id}/properties
{"key": "content-appearance-published", "value": "full-width"}
```

v2 API does NOT support setting properties inline during page creation.

**Content property API (for existing pages):**

```python
confluence.set_page_property(page_id, data={
    "key": "content-appearance-published",
    "value": "full-width",
    "version": {"number": 1}
})
```

### Experiment Result

Tested on page 2337112322: `full_width=True` works. Page renders wide.

---

## Finding 2: Table Formatting in Storage Format

### Table Layout Attribute

Storage format tables support `data-layout` attribute:

```xml
<table data-layout="full-width">
  ...
</table>
```

Values: `default`, `wide`, `full-width`.

### Column Widths via colgroup

Column widths are set using `<colgroup>` / `<col>` elements:

```xml
<table data-layout="full-width">
  <colgroup>
    <col style="width: 150px;" />
    <col style="width: 120px;" />
    <col style="width: 500px;" />
    <col style="width: 480px;" />
  </colgroup>
  <tbody>
    <tr><th><p>Header</p></th>...</tr>
    <tr><td><p>Cell</p></td>...</tr>
  </tbody>
</table>
```

Important notes:

- Pixel values work but act as **proportional** weights (not absolute)
- Percentage values reportedly do NOT work via API
- The `<col>` count must match the number of columns

### Experiment Result

Tested on page 2337112322: `data-layout="full-width"` + `<colgroup>`
with pixel widths works correctly. Column proportions match expectations.

### Comparison: Storage Format vs ADF

| Feature | Storage Format | ADF |
|---|---|---|
| Table layout | `<table data-layout="full-width">` | `table.attrs.layout` |
| Column width | `<col style="width: 150px;">` | `tableCell.attrs.colwidth: [150]` |
| Table width | Not directly supported | `table.attrs.width` (px) |
| Display mode | Not available | `table.attrs.displayMode` |

### Reference: AI Community Page Table Structure (ADF)

The well-formatted AI Community page uses:

```json
{
  "type": "table",
  "attrs": {"layout": "full-width"},
  "content": [{
    "type": "tableRow",
    "content": [
      {"type": "tableHeader", "attrs": {"colwidth": [153.6]}},
      {"type": "tableHeader", "attrs": {"colwidth": [128]}},
      {"type": "tableHeader", "attrs": {"colwidth": [512]}},
      {"type": "tableHeader", "attrs": {"colwidth": [486.4]}}
    ]
  }]
}
```

Total width: 153.6 + 128 + 512 + 486.4 = 1280px

---

## Finding 3: Current upload_confluence.py Gaps

### What's Missing

1. **No `full_width` parameter** passed to `create_page()` / `update_page()`
2. **No `data-layout`** on `<table>` element
3. **No `<colgroup>`** for column width control
4. **No CLI flag** for page width
5. **No frontmatter support** for table layout options

### Current Table Renderer

```python
def table(self, text):
    return f"<table>\n{text}</table>\n"

def table_cell(self, text, align=None, head=False):
    tag = "th" if head else "td"
    align_attr = f' align="{align}"' if align else ""
    return f"<{tag}{align_attr}>{text}</{tag}>\n"
```

### Design Challenge: Column Width Source

Markdown tables have no column width information. Options:

| Approach | Pros | Cons |
|---|---|---|
| Equal distribution | Simple, safe default | May not look optimal |
| Text length heuristic | Smarter sizing | Unpredictable, complex |
| Frontmatter config | Full control | Requires user config |
| Markdown dash count | Uses existing syntax | Fragile, non-standard |

**Recommendation**: Equal distribution as default + frontmatter override.

Frontmatter example:

```yaml
confluence:
  width: full          # page width
  table:
    layout: full-width # table layout
    colwidths: [12, 10, 40, 38]  # percentage ratios
```

---

## Finding 4: Storage Format Table Structure Notes

### thead vs tbody

Confluence Cloud storage format wraps header row in `<tbody>`, not
`<thead>`. The current renderer uses `<thead>` which may cause issues.

Observed in AI Community page (storage format view): headers use `<th>`
inside `<tbody>`, no `<thead>` wrapper.

### Cell Content Wrapping

Confluence expects cell content wrapped in `<p>` tags:

```xml
<!-- Correct -->
<td><p>Content here</p></td>

<!-- Current renderer output (may work but not canonical) -->
<td>Content here</td>
```

This is worth testing but may not cause visible issues.

---

## Summary of Verified Changes

| Change | Verified | Method |
|---|---|---|
| `full_width=True` on create/update | Yes | Tested on page 2337112322 |
| `<table data-layout="full-width">` | Yes | Tested on page 2337112322 |
| `<colgroup>` with pixel widths | Yes | Tested on page 2337112322 |
| Proportional width behavior | Yes | 150:120:500:480 ratio confirmed |

---

## References

- [Confluence Storage Format spec](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [ADF table node](https://developer.atlassian.com/cloud/jira/platform/apis/document/nodes/table/)
- [ADF tableCell node](https://developer.atlassian.com/cloud/jira/platform/apis/document/nodes/table_cell/)
- [atlassian-python-api docs](https://atlassian-python-api.readthedocs.io/confluence.html)
- [Set page width via REST](https://community.developer.atlassian.com/t/how-to-set-fixed-width-when-creating-new-page-with-rest-call/53591)
- [MCP page width feature request](https://github.com/sooperset/mcp-atlassian/issues/1086)
- [Compact Mode announcement (Feb 2026)](https://community.atlassian.com/forums/Confluence-articles/New-feature-Compact-Mode-and-Max-Width-to-support-information/ba-p/3190468)
