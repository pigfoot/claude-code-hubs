# Markdown-First Workflow (One-Way)

## Overview

The **Markdown-first workflow** is the official recommended approach for creating and publishing Confluence
documentation using AI tools like Claude Code. This workflow emphasizes local Markdown generation, human review, and
one-way publication to Confluence.

## Why Markdown-First?

**Official Recommendation:**
> "Always request Markdown generation first" - [Ivan Dachev's Claude Code MCP
> Guide](https://ivandachev.com/blog/claude-code-mcp-atlassian-integration)

**Key Benefits:**

- ✅ **Human-readable review**: Markdown is easier to read and edit than ADF JSON
- ✅ **Version control friendly**: Markdown files work well with Git
- ✅ **No macro loss**: One-way conversion avoids Confluence macro preservation issues
- ✅ **Quality control**: Team can validate content before publication
- ✅ **Code example testing**: Test all code snippets before publishing

## Recommended Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Analysis & Generation                                   │
│     Claude Code scans codebase                              │
│     Generates local Markdown files                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│  2. Review & Improvement                                    │
│     Team validates content                                  │
│     Test code examples                                      │
│     Add team-specific context                               │
│     Check for sensitive information                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│  3. Conversion & Publication                                │
│     Markdown → ADF/Storage Format                           │
│     Publish to Confluence                                   │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Options

### Option A: Official Atlassian MCP + External Converter

**Tools:**

- **MCP**: [Official Atlassian Remote MCP Server](https://github.com/atlassian/atlassian-mcp-server)
- **Converter**: [marklassian](https://marklassian.netlify.app/) (JavaScript) or
  `markdown_to_adf.py` (this plugin's built-in converter)

**Workflow:**

```bash
# 1. Generate Markdown locally with Claude
# 2. Review and edit the Markdown file
# 3. Convert and publish
npx marklassian input.md | \
  curl -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @- \
    https://your-site.atlassian.net/wiki/api/v2/pages
```

### Option B: Third-Party MCP (aashari)

**Tools:**

- **MCP**: [@aashari/mcp-server-atlassian-confluence](https://github.com/aashari/mcp-server-atlassian-confluence)

**Workflow:**

```javascript
// Use generic conf_post tool
conf_post({
  path: "/wiki/api/v2/pages",
  body: {
    title: "My Page",
    spaceId: "123456",
    body: {
      storage: {
        value: markdownToHtml(markdown),
        representation: "storage"
      }
    }
  }
})
```

### Option C: Python Scripts (Recommended for this plugin)

**Tools:**

- `markdown_to_adf.py` - Markdown to ADF converter (built-in)
- `confluence_adf_utils.py` - ADF upload helpers (built-in)
- REST API v2

**Workflow:**

```python
from markdown_to_adf import markdown_to_adf
from confluence_adf_utils import get_auth, create_page_adf

adf_body = markdown_to_adf(markdown_content)
base_url, auth = get_auth()
result = create_page_adf(base_url, auth, space_id, title, adf_body, parent_id=parent_id)
```

## Best Practices

### 1. Always Review Before Publishing

- Verify technical accuracy
- Test all code examples
- Check for exposed secrets/credentials
- Add team-specific context AI might miss

### 2. Use Strict Markdown Syntax

When converting Markdown for Confluence:

- **Lists and tables** must be delimited by blank lines before AND after
- **Nested lists** require proper indentation (2 or 4 spaces)
- **Code blocks** should specify language for syntax highlighting

Example:

```markdown
This is a paragraph.

- List item 1
- List item 2

This is another paragraph.
```

### 3. Version Control Integration

Store Markdown files in Git:

```
docs/
  confluence/
    project-overview.md
    api-reference.md
    deployment-guide.md
```

Use GitHub Actions for automated sync:

```yaml
- uses: Telefonica/markdown-confluence-sync-action@v2
  with:
    confluence-url: ${{ secrets.CONFLUENCE_URL }}
    confluence-token: ${{ secrets.CONFLUENCE_TOKEN }}
    docs-path: docs/confluence/
```

### 4. Handle Automation Notices

Add notices to Confluence pages managed by automation:

```markdown
> ⚠️ **Note**: This page is automatically generated from source code documentation.
> Manual edits will be overwritten on the next sync.
> Edit the source Markdown file instead: [link to repo]
```

## Limitations

### What Gets Lost in One-Way Markdown Conversion

When converting Markdown → Confluence (one-way upload), these limitations apply
to the **Markdown conversion step** specifically:

- ❌ Confluence-specific macros (unless using raw ADF blocks)
- ❌ Page properties
- ❌ Custom layouts
- ❌ Expand/Info/Warning panels (unless converted to equivalents)

> **Note:** These limitations are inherent to Markdown as a format. For editing
> existing pages that contain these elements, use Method 6 (ADF JSON diff) or
> Method 7 (ADF-native roundtrip) instead of Markdown-based methods.

### When NOT to Use Markdown-First

- **Existing pages with complex macros**: Use Method 6 (ADF JSON diff) for text edits that
  preserve macros, or Method 7 (ADF-native roundtrip with markers) for full document
  editing. Confluence web editor is also an option for manual edits.
- **Pages requiring live data**: Use Confluence macros (e.g., JIRA issues, status reports)
- **Collaborative editing**: Use Confluence's collaborative features

> **Note:** Storage Format is NOT deprecated. The v2 API fully supports
> `representation: storage` for GET/PUT/POST. Only the v1 API *endpoints* are being
> deprecated. The MCP Gateway only supports ADF format, but the REST API v2 supports
> both Storage Format and ADF.

## Common Issues

### Issue: Markdown Syntax Not Rendering

**Problem**: Lists, tables, or code blocks not rendering correctly

**Solution**: Ensure blank lines surround block elements

```markdown
# Correct
Paragraph text.

- List item

Another paragraph.

# Incorrect
Paragraph text.
- List item
Another paragraph.
```

### Issue: Code Blocks Without Syntax Highlighting

**Problem**: Code appears as plain text

**Solution**: Specify language in fence blocks

````markdown
```python
def hello():
    print("Hello, world!")
```
````

### Issue: Confluence API v1 Deprecation

**Problem**: Tools using deprecated API endpoints fail after March 31, 2025

**Solution**: Migrate to REST API v2

- Replace `body.view` with `body.storage`
- Update endpoint URLs from `/rest/api/` to `/wiki/api/v2/`

## References

- [Ivan Dachev's Complete Guide](https://ivandachev.com/blog/claude-code-mcp-atlassian-integration)
- [Markdown Confluence Tools](https://markdown-confluence.com/)
- [markdown_to_adf.py](../scripts/markdown_to_adf.py) - Built-in Markdown to ADF converter
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Atlassian REST API v2 Migration](https://developer.atlassian.com/cloud/confluence/deprecation-notice-rest-api-v1/)
- [GitHub Actions Markdown Sync](https://github.com/Telefonica/markdown-confluence-sync-action)

## Related Documentation

- [Roundtrip Workflow](./roundtrip-workflow.md) - For editing existing pages
- [CQL Reference](./cql_reference.md) - For searching Confluence content
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
