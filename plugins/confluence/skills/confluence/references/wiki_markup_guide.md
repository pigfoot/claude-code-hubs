# Wiki Markup Quick Reference

## Text Formatting

| Markdown | Wiki Markup | Result |
|----------|-------------|--------|
| `**bold**` | `*bold*` | **bold** |
| `*italic*` | `_italic_` | *italic* |
| `` `code` `` | `{{code}}` | `code` |
| `~~strike~~` | `-strike-` | ~~strike~~ |
| `^super^` | `^super^` | superscript |
| `~sub~` | `~sub~` | subscript |

## Headings

```wiki
h1. Heading 1
h2. Heading 2
h3. Heading 3
h4. Heading 4
h5. Heading 5
h6. Heading 6
```

## Links

| Type | Wiki Markup |
|------|-------------|
| External | `[Google\|https://google.com]` |
| Same text as URL | `[https://google.com]` |
| Page link | `[Page Title]` |
| Anchor | `[#anchor]` |
| Attachment | `[^filename.pdf]` |

## Images

```wiki
!image.png!                    -- basic
!image.png|width=300!          -- with width
!image.png|thumbnail!          -- thumbnail
!http://example.com/img.png!   -- external URL
```

## Lists

**Unordered:**

```wiki
* Item 1
* Item 2
** Nested item
** Another nested
* Item 3
```

**Ordered:**

```wiki
# First
# Second
## Nested numbered
# Third
```

## Tables

```wiki
||Header 1||Header 2||Header 3||
|Cell 1|Cell 2|Cell 3|
|Cell 4|Cell 5|Cell 6|
```

## Code Blocks

```wiki
{code:language=python}
def hello():
    print("Hello, World!")
{code}
```

Supported languages: `java`, `javascript`, `python`, `sql`, `bash`, `xml`, `json`, etc.

## Panels

```wiki
{info}
Information panel content
{info}

{note}
Note panel content
{note}

{warning}
Warning panel content
{warning}

{tip}
Tip panel content
{tip}
```

## Macros

**Table of Contents:**

```wiki
{toc}
```

**Expand/Collapse:**

```wiki
{expand:Click to expand}
Hidden content here
{expand}
```

**Status:**

```wiki
{status:colour=Green|title=Complete}
{status:colour=Yellow|title=In Progress}
{status:colour=Red|title=Blocked}
```

## Horizontal Rule

```wiki
----
```

## Line Break

```wiki
First line\\
Second line
```

## Escaping

Use backslash to escape special characters:

```wiki
\*not bold\*
\{not a macro\}
```
