# Confluence Macro Preservation Guide

Complete documentation on which macros are preserved or lost during Markdown ↔ Confluence conversion, and how to
preserve specific macros.

---

## Quick Overview

| Macro Type | Conversion Status | Preservation Method |
|-----------|---------|---------|
| **Code Block** | ✅ Auto-converted | Markdown fence blocks |
| **Table of Contents** | ✅ Auto-converted | `[TOC]` or doctoc |
| **Info/Warning/Error Panels** | ✅ Auto-converted | Blockquotes + keywords |
| **Images (attachments)** | ✅ Auto-uploaded | Markdown images |
| **Comments** | ✅ Auto-converted | HTML comments |
| **Page Properties** | ❌ Lost | Requires manual raw ADF/CSF |
| **Expand Macro** | ❌ Lost | Requires manual raw ADF/CSF |
| **Jira Issue Macro** | ❌ Lost | Cannot convert (dynamic content) |
| **Custom Layouts** | ❌ Lost | Cannot convert |
| **Third-party Macros** | ❌ Lost | Cannot convert |

---

## 1. Auto-Converted Macros

These macros can be automatically converted through standard Markdown syntax, **roundtrip conversion basically preserved**.

### 1.1 Code Block Macro

#### Markdown → Confluence

````markdown
```python
def hello():
```
````

```
print("Hello, World!")

```

#### Converts to Confluence

```xml
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:parameter ac:name="theme">Midnight</ac:parameter>
  <ac:parameter ac:name="linenumbers">true</ac:parameter>
  <ac:plain-text-body><![CDATA[
def hello():
    print("Hello, World!")
  ]]></ac:plain-text-body>
</ac:structured-macro>
```

#### Confluence → Markdown

Correctly converts back to fence code block.

**Preservation Level:** ✅ Fully preserved

- ✅ Syntax highlighting
- ✅ Code content
- ⚠️ Theme settings may be lost (defaults to Midnight)
- ⚠️ Title may be lost

---

### 1.2 Table of Contents (TOC) Macro

#### Markdown → Confluence

```markdown
[TOC]
```

Or using doctoc comments:

```markdown
<!-- START doctoc -->
<!-- END doctoc -->
```

#### Converts to Confluence

```xml
<ac:structured-macro ac:name="toc">
  <ac:parameter ac:name="printable">true</ac:parameter>
  <ac:parameter ac:name="style">disc</ac:parameter>
  <ac:parameter ac:name="maxLevel">7</ac:parameter>
  <ac:parameter ac:name="minLevel">1</ac:parameter>
</ac:structured-macro>
```

#### Confluence → Markdown

Usually converts to `[TOC]` or removed (as Markdown doesn't need TOC macro).

**Preservation Level:** ⚠️ Partially preserved

- ✅ TOC functionality preserved
- ❌ Custom parameters (min/max level) lost
- ❌ Style settings lost

---

### 1.3 Info/Warning/Error/Note Panels

#### Markdown → Confluence

Using blockquote + keywords:

```markdown
> **Warning**: This is a warning message.

> **Note**: This is an informational note.

> **Error**: This is an error message.

> **Success**: This operation completed successfully.
```

Or using GitHub-flavored alerts:

```markdown
> [!NOTE]
> This is a note

> [!WARNING]
> This is a warning

> [!IMPORTANT]
> Critical information
```

#### Converts to Confluence

```xml
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>This is a note</p>
  </ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="warning">
  <ac:rich-text-body>
    <p>This is a warning</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

#### Confluence → Markdown

Usually converts back to blockquote, but may lose color information.

**Preservation Level:** ⚠️ Partially preserved

- ✅ Content preserved
- ⚠️ Panel type may be lost (becomes regular blockquote)
- ❌ Icons lost

#### Mapping

| Markdown | Confluence Panel |
|----------|-----------------|
| `> **Note**:` | Info panel (blue) |
| `> **Warning**:` | Note panel (yellow) |
| `> **Error**:` | Warning panel (red) |
| `> **Success**:` | - (no equivalent, may become info) |

---

### 1.4 Images & Attachments

#### Markdown → Confluence

```markdown
![Alt text](image.png)
```

#### Converts to Confluence

- Images automatically uploaded as page attachments
- URL converted to Confluence format:

```xml
<ac:image>
  <ri:attachment ri:filename="image.png" />
</ac:image>
```

#### Confluence → Markdown

```markdown
![](attachments/image.png)
```

**Preservation Level:** ✅ Fully preserved

- ✅ Image content
- ✅ Alt text
- ⚠️ Size settings may be lost
- ⚠️ Alignment settings lost

---

### 1.5 HTML Comments (Placeholder)

#### Markdown → Confluence

```markdown
<!-- This is a hidden comment -->
```

#### Converts to Confluence

```xml
<ac:placeholder>This is a hidden comment</ac:placeholder>
```

#### Confluence → Markdown

Converts back to HTML comment.

**Preservation Level:** ✅ Fully preserved

---

## 2. Macros That Will Be Lost

These macros **cannot** be converted through standard Markdown, roundtrip will lose them.

### 2.1 Page Properties Macro

#### Confluence Storage Format

```xml
<ac:structured-macro ac:name="details">
  <ac:rich-text-body>
    <table>
      <tr>
        <th>Owner</th>
        <td>John Doe</td>
      </tr>
      <tr>
        <th>Status</th>
        <td>In Progress</td>
      </tr>
    </table>
  </ac:rich-text-body>
</ac:structured-macro>
```

#### Markdown → Confluence

Becomes a regular table, loses page properties functionality.

#### Confluence → Markdown

```markdown
| Owner | John Doe |
| Status | In Progress |
```

**Preservation Level:** ❌ Lost

- ❌ Page properties functionality lost
- ✅ Content preserved (becomes regular table)
- ❌ Cannot be used in page properties report

---

### 2.2 Expand Macro

#### Confluence Storage Format

```xml
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body>
    <p>Hidden content here...</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

#### Markdown → Confluence

No equivalent syntax, becomes:

```markdown
**Click to expand**

Hidden content here...
```

#### Confluence → Markdown

Expanded content displayed directly, loses collapse functionality.

**Preservation Level:** ❌ Lost

- ✅ Content preserved
- ❌ Collapse/expand functionality lost

#### Alternative

Use HTML `<details>` tag (some tools support):

```markdown
<details>
<summary>Click to expand</summary>

Hidden content here...
</details>
```

---

### 2.3 Jira Issue Macro

#### Confluence Storage Format

```xml
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="key">PROJ-123</ac:parameter>
</ac:structured-macro>
```

#### Markdown → Confluence

Cannot create (requires dynamic Jira connection).

#### Confluence → Markdown

Usually converts to plain text or link:

```markdown
[PROJ-123](https://jira.example.com/browse/PROJ-123)
```

**Preservation Level:** ❌ Completely lost

- ❌ Dynamic content lost
- ❌ Status display lost
- ⚠️ May convert to static link

---

### 2.4 Custom Layouts (Sections/Columns)

#### Confluence Storage Format

```xml
<ac:layout>
  <ac:layout-section ac:type="two_equal">
    <ac:layout-cell>
      <p>Left column</p>
    </ac:layout-cell>
    <ac:layout-cell>
      <p>Right column</p>
    </ac:layout-cell>
  </ac:layout-section>
</ac:layout>
```

#### Markdown → Confluence

No equivalent syntax.

#### Confluence → Markdown

Becomes linear content:

```markdown
Left column

Right column
```

**Preservation Level:** ❌ Completely lost

- ✅ Content preserved
- ❌ Layout lost

---

### 2.5 Status Macro (Label/Badge)

#### Confluence Storage Format

```xml
<ac:structured-macro ac:name="status">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">Complete</ac:parameter>
</ac:structured-macro>
```

#### Markdown → Confluence

No equivalent syntax, may become:

```markdown
**Complete**
```

#### Confluence → Markdown

Becomes bold text, loses color and style.

**Preservation Level:** ❌ Lost

- ✅ Text content preserved
- ❌ Color lost
- ❌ Badge style lost

---

### 2.6 Drawio/Gliffy Diagrams

#### Confluence Storage Format

```xml
<ac:structured-macro ac:name="drawio">
  <ac:parameter ac:name="diagramName">architecture.drawio</ac:parameter>
</ac:structured-macro>
```

#### Markdown → Confluence

Cannot create (requires Drawio data).

#### Confluence → Markdown

- If Drawio has PNG export, may convert to image
- Otherwise completely lost

**Preservation Level:** ❌ Lost

- ⚠️ May preserve PNG (but not editable)
- ❌ Editable XML metadata lost

#### Exception

Draw.io diagrams can roundtrip if PNG contains editable XML metadata (mentioned in official docs).

---

## 3. How to Preserve Complex Macros

### Method 1: Raw ADF Blocks (Recommended)

Embed native ADF JSON in Markdown.

#### Syntax

````markdown
```adf
{
  "type": "expand",
  "attrs": {"title": "Click to expand"},
  "content": [
```
{
  "type": "paragraph",
  "content": [
    {"type": "text", "text": "Hidden content"}
  ]
}
```
  ]
}
```
````

#### Example: Expand Macro

````markdown
```adf
{
  "type": "expand",
  "attrs": {"title": "Advanced Options"},
  "content": [
```
{
  "type": "paragraph",
  "content": [
    {"type": "text", "text": "Advanced configuration settings..."}
  ]
}
```
  ]
}
```
````

#### Example: Decision List

````markdown
```adf
{
  "type": "decisionList",
  "attrs": {"localId": "unique-id-here"},
  "content": [
```
{
  "type": "decisionItem",
  "attrs": {"state": "DECIDED", "localId": "item-id"},
  "content": [{"type": "text", "text": "Decision to track"}]
}
```
  ]
}
```
````

#### How to Find ADF Structure

1. Check [Atlassian ADF Documentation](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
2. Browse [@atlaskit/adf-schema](https://unpkg.com/browse/@atlaskit/adf-schema@25.6.0/dist/types/schema/nodes/)
3. Extract ADF from existing page:

   ```
   GET https://your-site.atlassian.net/wiki/rest/api/content/{page-id}?expand=body.atlas_doc_format
   ```

---

### Method 2: Raw CSF Blocks (Confluence Storage Format)

Embed native Storage Format XML in Markdown.

#### Syntax

````markdown
```csf
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body>
```
<p>Hidden content</p>
```
  </ac:rich-text-body>
</ac:structured-macro>
```
````

#### Example: Page Properties

````markdown
```csf
<ac:structured-macro ac:name="details">
  <ac:rich-text-body>
```
<table>
  <tr>
    <th>Owner</th>
    <td>John Doe</td>
  </tr>
  <tr>
    <th>Due Date</th>
    <td>2025-12-31</td>
  </tr>
</table>
```
  </ac:rich-text-body>
</ac:structured-macro>
```
````

#### Example: Status Macro

````markdown
```csf
<ac:structured-macro ac:name="status">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">Approved</ac:parameter>
</ac:structured-macro>
```
````

---

### Method 3: Hybrid Approach (Recommended for Roundtrip)

#### Strategy

1. Use Markdown for simple content
2. Use raw ADF/CSF blocks for complex macros
3. Identify and protect raw blocks during editing

#### Example Document

````markdown
## API Documentation

This is a regular paragraph in Markdown.

```python

# Regular code block (converts to code macro)

def example():
```

> **Note**: This becomes an info panel.

```adf
```
pass
```
{
  "type": "expand",
  "attrs": {"title": "Advanced Configuration"},
  "content": [...]
}
```

```csf
<ac:structured-macro ac:name="details">
  <ac:rich-text-body>
```
<table>...</table>
```
  </ac:rich-text-body>
</ac:structured-macro>
```
````

#### Roundtrip Editing Logic

```python
def safe_roundtrip_edit(markdown: str, edit_fn) -> str:
    # 1. Extract and protect raw blocks
    protected_blocks = []
    cleaned_markdown = extract_raw_blocks(markdown, protected_blocks)

    # 2. Edit cleaned markdown
    edited = edit_fn(cleaned_markdown)

    # 3. Restore raw blocks
    final = restore_raw_blocks(edited, protected_blocks)

    return final
```

---

## 4. Macro Preservation Decision Matrix

### Decision Flow

```
Need to preserve a macro?
│
├─→ Is it simple content (code, list, heading)?
│   └─→ Yes: Use standard Markdown ✅
│
├─→ Is it info/warning panel?
│   └─→ Yes: Use blockquote + keywords ✅
│
├─→ Is it dynamic content (Jira, status report)?
│   └─→ Yes: Cannot preserve, edit directly in Confluence ❌
│
├─→ Is it complex but static macro (expand, page properties)?
│   └─→ Yes: Use raw ADF/CSF blocks ⚠️
│
└─→ Is it layout (layouts, columns)?
    └─→ Yes: Recommend editing directly in Confluence ❌
```

### Recommendations by Usage Frequency

| Macro | Preservation Recommendation | Reason |
|-------|---------|------|
| **Code Block** | ✅ Markdown | High frequency, perfect conversion |
| **Info Panel** | ✅ Blockquote | Common, partial preservation sufficient |
| **TOC** | ✅ `[TOC]` | Confluence will rebuild |
| **Expand** | ⚠️ Raw ADF | Medium frequency, worth preserving |
| **Page Properties** | ⚠️ Raw CSF | Medium frequency, worth preserving |
| **Status Macro** | ❌ Manual | Low frequency, add back manually |
| **Layouts** | ❌ Manual | Low frequency, faster to edit in Confluence |
| **Jira Issues** | ❌ Manual | Dynamic content, cannot preserve |

---

## 5. Practical Recommendations

### Recommendation 1: Check if Page is Safe for Roundtrip

```python
def is_safe_for_roundtrip(page_content: str) -> tuple[bool, list[str]]:
    """
    Check if page can safely roundtrip
    Returns: (is_safe, list_of_issues)
    """
    issues = []

    # Check for macros that will be lost
    if '<ac:structured-macro ac:name="details"' in page_content:
        issues.append("Contains page properties macro (will be lost)")

    if '<ac:structured-macro ac:name="jira"' in page_content:
        issues.append("Contains Jira macro (will be lost)")

    if '<ac:layout>' in page_content:
        issues.append("Contains custom layouts (will be lost)")

    if '<ac:structured-macro ac:name="expand"' in page_content:
        issues.append("Contains expand macro (will be lost)")

    if '<ac:structured-macro ac:name="status"' in page_content:
        issues.append("Contains status macro (will be lost)")

    # Macros that can be preserved don't count as issues
    # (code, toc, info/warning panels, etc.)

    return len(issues) == 0, issues
```

### Recommendation 2: Build Macro Protection Mechanism

```python
import re

def protect_raw_blocks(markdown: str) -> tuple[str, dict]:
    """
    Extract and protect raw ADF/CSF blocks
    """
    protected = {}
    counter = 0

    def replace_block(match):
        nonlocal counter
        placeholder = f"<<<PROTECTED_BLOCK_{counter}>>>"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder

    # Protect adf blocks
    markdown = re.sub(
        r'```adf\n(.*?)\n```',
        replace_block,
        markdown,
        flags=re.DOTALL
    )

    # Protect csf blocks
    markdown = re.sub(
        r'```csf\n(.*?)\n```',
        replace_block,
        markdown,
        flags=re.DOTALL
    )

    return markdown, protected

def restore_raw_blocks(markdown: str, protected: dict) -> str:
    """
    Restore protected blocks
    """
    for placeholder, original in protected.items():
        markdown = markdown.replace(placeholder, original)
    return markdown
```

### Recommendation 3: Warn User Before Edit

```python
def warn_user_before_edit(page_id: str):
    """
    Warn user before editing
    """
    page = get_page(page_id)
    is_safe, issues = is_safe_for_roundtrip(page['body']['storage']['value'])

    if not is_safe:
        print("⚠️  Warning: This page contains macros that will be lost:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRecommendations:")
        print("  1. Edit this page directly in Confluence")
        print("  2. Use raw ADF/CSF blocks to preserve macros")
        print("  3. Backup the page before proceeding")

        proceed = input("\nProceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Cancelled")
            exit(1)
```

---

## 6. Test Cases

### Test 1: Code Block Roundtrip

```python
def test_code_block_roundtrip():
    markdown = """
## Example

\u0060\u0060\u0060python
def hello():
\u0060\u0060\u0060

"""

    # Markdown → Confluence
    storage = markdown_to_storage(markdown)
    assert '<ac:structured-macro ac:name="code"' in storage

    # Confluence → Markdown
    result = storage_to_markdown(storage)
    assert '```python' in result
    assert 'def hello():' in result

    # Compare
    assert result.strip() == markdown.strip()
```

### Test 2: Info Panel Roundtrip

```python
def test_info_panel_roundtrip():
    markdown = '''
> **Note**: This is important.
'''

    storage = markdown_to_storage(markdown)
    assert '<ac:structured-macro ac:name="info"' in storage

    result = storage_to_markdown(storage)
    # May lose "Note:" label, only blockquote remains
    assert '> ' in result or 'important' in result
```

### Test 3: Expand Macro (Will Be Lost)

```python
def test_expand_macro_loss():
    storage = '''
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Details</ac:parameter>
  <ac:rich-text-body><p>Hidden</p></ac:rich-text-body>
</ac:structured-macro>
'''

    markdown = storage_to_markdown(storage)
    # Expanded content displayed directly
    assert 'Hidden' in markdown
    # Collapse functionality lost
    assert 'expand' not in markdown.lower()

    # Cannot recover after roundtrip
    storage2 = markdown_to_storage(markdown)
    assert '<ac:structured-macro ac:name="expand"' not in storage2
```

---

## 7. Reference Resources

### Official Documentation

- [Atlassian Document Format (ADF) Structure](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [@atlaskit/adf-schema](https://unpkg.com/browse/@atlaskit/adf-schema@25.6.0/dist/types/schema/nodes/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)

### Tool Documentation

- [Markdown Confluence Tools - Raw ADF](https://markdown-confluence.com/features/raw-adf.html)
- [md_to_conf - Markdown Syntax](https://spydersoft-consulting.github.io/md_to_conf/markdown-syntax/)
- [md2cf Documentation](https://pypi.org/project/md2cf/)

### Community Resources

- [Converting Markdown to ADF: Complete Guide](https://adfapi.dev/blog/2025/11/converting-markdown-to-adf-complete-guide/)
- [Confluence Community - Macro Discussions](https://community.atlassian.com/forums/Confluence-questions/)

---

## Summary

### Reliably Preserved (Roundtrip OK)

✅ Code blocks
✅ Images
✅ HTML comments
✅ Basic formatting (bold, italic, lists)

### Partially Preserved (May Lose Details)

⚠️ Table of Contents
⚠️ Info/Warning panels
⚠️ Links (anchors may change)

### Will Be Lost (Requires Manual Handling)

❌ Page properties
❌ Expand macro
❌ Status macro
❌ Jira issue macro
❌ Custom layouts
❌ Third-party macros

### Preservation Strategies

1. **Simple edits**: Use standard Markdown (accept macro loss)
2. **Full preservation**: Use raw ADF/CSF blocks
3. **Hybrid approach**: Use raw blocks for important macros, Markdown for rest
4. **Avoid roundtrip**: Edit complex pages directly in Confluence
