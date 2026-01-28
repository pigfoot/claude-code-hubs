# Confluence Workflow & Tools Comparison

## 1. Workflow Comparison: Markdown-First vs Roundtrip

| Feature | Markdown-First (One-way) | Roundtrip (Bidirectional) |
|-----|---------------------|----------------|
| **Use Case** | Creating new documents, major rewrites | Editing existing documents |
| **Workflow** | Generate locally → Review → Publish | Read → Edit → Write back |
| **Macro Preservation** | N/A (newly created) | ❌ Lost |
| **Conversion Quality** | ⭐⭐⭐⭐⭐ (stable one-way conversion) | ⭐⭐⭐ (may be lossy) |
| **Human Review** | ✅ Mandatory review | ⚠️ Optional review |
| **Version Control** | ✅ Markdown in Git | ⚠️ Can only commit after conversion |
| **Code Testing** | ✅ Test before publishing | ⚠️ Harder to test |
| **Complexity** | Simple | Medium to High |
| **Official Recommendation** | ✅ Recommended | ⚠️ Use with caution |
| **Suitable Page Types** | Documentation, tutorials, API docs | Simple text updates |
| **Not Suitable For** | - | Pages with macros, page properties, complex layouts |

### Recommended Decision Flow

```
Creating new document?
  └─→ Markdown-First

Editing existing document?
  ├─→ Has macros/properties?
  │    └─→ Yes: Edit directly in Confluence web UI
  │    └─→ No: Check edit type
  │         ├─→ Simple text update: Roundtrip OK
  │         └─→ Major rewrite: Consider Markdown-First
  └─→
```

---

## 2. MCP Server Comparison

| Feature | Official Atlassian MCP | @aashari MCP | sooperset MCP |
|-----|----------------------|-------------|--------------|
| **Maintainer** | Atlassian (Official) | Andi Ashari (Community) | sooperset (Community) |
| **Hosting** | Cloud (Remote) | Self-hosted (Local) | Self-hosted (Local) |
| **Supported Products** | Jira + Confluence + Compass | Confluence only | Jira + Confluence |
| **Authentication** | OAuth 2.1 | API Token | API Token |
| **Setup Complexity** | Low (browser authorization) | Medium (requires token generation) | Medium (requires token generation) |
| **Enterprise Support** | ✅ Official support | ❌ Community maintained | ❌ Community maintained |
| **Tool Type** | High-level (semantic) | Low-level (HTTP methods) | High-level (semantic) |
| **Markdown Conversion** | ❌ No (returns ADF) | ❌ No (claims to but not implemented) | ✅ Has option to skip conversion |
| **Downloads** | - | 15.2k+ | - |
| **Update Frequency** | High | Medium | Medium |
| **Best For** | Enterprise, multi-product integration | Lightweight Confluence-only use | Python projects, need Jira |
| **GitHub** | [atlassian/atlassian-mcp-server](https://github.com/atlassian/atlassian-mcp-server) | [aashari/mcp-server-atlassian-confluence](https://github.com/aashari/mcp-server-atlassian-confluence) | [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian) |

### Tool Type Explanation

**High-level tools (semantic)**:

```javascript
// Example: Search pages
searchConfluence({query: "API documentation"})
getPage({pageId: "123456"})
```

**Low-level tools (HTTP methods)**:

```javascript
// Example: Manually build API request
conf_get({
  path: "/wiki/api/v2/pages/123456",
  queryParams: {expand: "body.storage"}
})
```

---

## 3. Implementation Methods Comparison (Roundtrip)

| Aspect | Method 1: REST API + Storage | Method 2: MCP + ADF | Method 3: Pragmatic Hybrid |
|-----|------------------------|----------------|---------------------|
| **Read Method** | REST API v2 | MCP getConfluencePage | MCP getConfluencePage |
| **Format** | Storage Format (XHTML) | ADF (JSON) | ADF (JSON, direct manipulation) |
| **Conversion Tools** | confluence-to-markdown<br>md2cf | atlas-doc-parser (Python)<br>marklassian (JavaScript) | None (Claude understands JSON directly) |
| **Write Method** | REST API v2 | MCP updateConfluencePage | MCP updateConfluencePage |
| **Language Requirements** | Python | Python + JavaScript | Python (MCP wrapper) |
| **Setup Complexity** | ⭐⭐⭐ (API token) | ⭐⭐⭐⭐ (dual-language environment) | ⭐⭐ (MCP already set up) |
| **Conversion Quality** | ⭐⭐⭐⭐ (best) | ⭐⭐⭐ | ⭐⭐ (simple edits only) |
| **Macro Preservation** | ❌ | ❌ | ❌ |
| **Maturity** | ⭐⭐⭐⭐⭐ (battle-tested) | ⭐⭐⭐ (newer tools) | ⭐⭐ (experimental) |
| **Best For** | Production environment, complex edits | MCP-first architecture | Simple edits, quick prototypes |
| **Implementation Time** | Medium | High | Low |
| **Maintenance Cost** | Low | Medium | Low |

### Recommended Selection

```
Need production-grade quality?
  └─→ Method 1 (REST API + Storage Format)

Already using MCP and don't want REST API?
  └─→ Method 2 (MCP + ADF)

Just simple edit testing?
  └─→ Method 3 (Pragmatic Hybrid)
```

---

## 4. Authentication Methods Comparison

| Aspect | OAuth 2.1 (Official MCP) | API Token (REST API / Third-party MCP) |
|-----|-------------------|--------------------------------|
| **Setup Steps** | 1. Run `/mcp`<br>2. Select atlassian<br>3. Browser authorization | 1. Login to Atlassian<br>2. Generate API Token<br>3. Set environment variables |
| **User Experience** | ⭐⭐⭐⭐⭐ Simple (click to authorize) | ⭐⭐⭐ Requires copying/pasting token |
| **Security** | ⭐⭐⭐⭐⭐ Most secure (standard OAuth) | ⭐⭐⭐⭐ Secure (requires proper storage) |
| **Permission Control** | Fine-grained (based on authorization scope) | Same as user's full permissions |
| **Expiration Handling** | Automatic refresh (refresh token) | Manual update (no expiration reminder) |
| **Revocation Method** | Revoke in Atlassian account settings | Revoke in Atlassian account settings |
| **Multi-environment Support** | Requires re-authorization | Easy (copy token) |
| **CI/CD Integration** | ⭐⭐ Difficult | ⭐⭐⭐⭐⭐ Easy |
| **Best For** | Personal use, IDE integration | Automation, CI/CD, scripts |

### Setup Guide

**OAuth 2.1 Setup**:

```bash
# One-time setup
claude mcp add atlassian \
  --transport sse \
  "https://mcp.atlassian.com/v1/sse" \
  --scope user

# Or use /mcp interactive menu
/mcp
# Select "atlassian" → "Authenticate"
```

**API Token Setup**:

```bash
# 1. Generate token
# https://id.atlassian.com/manage-profile/security/api-tokens

# 2. Set environment variables
export CONFLUENCE_URL="https://your-site.atlassian.net"
export CONFLUENCE_USER="your@email.com"
export CONFLUENCE_API_TOKEN="your_api_token_here"

# 3. Or write to ~/.claude/settings.json
{
  "env": {
    "CONFLUENCE_URL": "https://your-site.atlassian.net",
    "CONFLUENCE_USER": "your@email.com",
    "CONFLUENCE_API_TOKEN": "your_token"
  }
}
```

---

## 5. Conversion Tools Comparison

### Markdown → Confluence

| Tool | Language | Target Format | Maturity | Features |
|-----|------|---------|-------|------|
| **md2cf** | Python | Storage Format | ⭐⭐⭐⭐⭐ | Battle-tested, based on mistune |
| **markdown-to-confluence** | Python | Storage Format | ⭐⭐⭐⭐ | REST API v2, supports GitHub Actions |
| **marklassian** | JavaScript | ADF | ⭐⭐⭐⭐ | Lightweight, designed for ADF |
| **markdown-confluence** | JavaScript | ADF | ⭐⭐⭐⭐ | CLI + Library, multiple integrations |

### Confluence → Markdown

| Tool | Language | Source Format | Maturity | Features |
|-----|------|---------|-------|------|
| **confluence-to-markdown-converter** | Java/XSLT | Storage Format | ⭐⭐⭐⭐ | XSLT-based, customizable |
| **atlas-doc-parser** | Python | ADF | ⭐⭐⭐ | Designed for AI, object-oriented API |
| **adf-to-md** | JavaScript | ADF | ⭐⭐⭐ | Simple, lightweight |
| **html2text** | Python | HTML/Storage | ⭐⭐⭐⭐⭐ | General HTML conversion tool |

### Bidirectional Conversion

| Tool | Language | Supported Directions | Roundtrip Quality | Notes |
|-----|------|---------|--------------|------|
| **extended-markdown-adf-parser** | JavaScript | MD ↔ ADF | ⭐⭐⭐⭐ | Claims "complete round-trip fidelity" |
| **md2cf + html2text** | Python | MD ↔ Storage | ⭐⭐⭐ | Combined solution, macros will be lost |
| **@atlaskit/editor-markdown-transformer** | JavaScript | MD ↔ ADF | ⭐⭐⭐⭐ | Official Atlassian, but complex |

---

## 6. Format Comparison

| Format | Full Name | Type | Readability | Macro Support | API Support |
|-----|---------|------|-------|-----------|---------|
| **Markdown** | Markdown | Plain text | ⭐⭐⭐⭐⭐ | ❌ | ❌ (requires conversion) |
| **ADF** | Atlassian Document Format | JSON | ⭐⭐ | ✅ (partial) | ✅ (v2 API) |
| **Storage Format** | Confluence Storage Format | XHTML-based XML | ⭐⭐⭐ | ✅ (complete) | ✅ (v1/v2 API) |
| **View Format** | - | Rendered HTML | ⭐⭐⭐⭐ | ✅ (rendered) | ✅ (read-only) |
| **Wiki Markup** | Confluence Wiki Markup | Plain text | ⭐⭐⭐⭐ | ✅ (legacy) | ⚠️ (deprecated) |

### Format Examples

**Markdown**:

```markdown
## Heading

This is a paragraph with **bold** text.

- Item 1
- Item 2
```

**ADF (JSON)**:

```json
{
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [{"type": "text", "text": "Heading"}]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "This is a paragraph with "},
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " text."}
      ]
    }
  ]
}
```

**Storage Format (XHTML)**:

```xml
<h2>Heading</h2>
<p>This is a paragraph with <strong>bold</strong> text.</p>
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>
```

---

## 7. Use Case Decision Matrix

| Use Case | Recommended Workflow | Recommended Method | Recommended Auth |
|---------|------------|---------|---------|
| Create API documentation | Markdown-First | Python scripts (md2cf) | API Token |
| Create tutorials | Markdown-First | Python scripts (md2cf) | API Token |
| Update simple text | Roundtrip | Method 3 (Pragmatic) | OAuth (MCP) |
| Batch update multiple pages | Roundtrip | Method 1 (REST API) | API Token |
| Fix typos | Roundtrip | Method 3 (Pragmatic) | OAuth (MCP) |
| Rewrite pages with macros | Manual (Confluence Web UI) | - | - |
| CI/CD auto-publish | Markdown-First | Python scripts + API | API Token |
| Edit in IDE | Roundtrip | MCP | OAuth |
| Team collaboration documents | Markdown-First + Git | Python scripts + GitHub Actions | API Token |
| One-time migration | Markdown-First | Python scripts (batch) | API Token |

---

## 8. Cost & Performance Comparison

| Metric | Official MCP (OAuth) | Third-party MCP | REST API Direct |
|-----|---------------------|----------------|----------------|
| **Token Usage** | High (verbose responses) | Medium (TOON format saves tokens) | Low (you control it) |
| **API Rate Limit** | Atlassian controlled | User's own API quota | User's own API quota |
| **Network Latency** | Medium (cloud MCP relay) | Low (local MCP) | Low (direct API) |
| **Setup Cost** | Low (one-time authorization) | Medium (generate token) | Medium (generate token) |
| **Maintenance Cost** | Low (officially maintained) | Medium (community maintained) | High (self-maintained) |
| **Learning Curve** | Low (high-level API) | Low (HTTP methods) | High (need to understand REST API) |

---

## 9. Recommended Configuration for This Plugin

Based on the above analysis, recommended configuration:

```yaml
Primary Workflow:
  - Markdown-First (for creating new documents)

Secondary Workflow:
  - Roundtrip (for simple edits)

MCP Server:
  - Official Atlassian MCP
  - Reason: OAuth is simple, official support, future stability

Roundtrip Method:
  - Method 1 (REST API + Storage Format)
  - Reason: Best conversion quality, mature tools

Tools to Implement:
  - scripts/md2cf.py (Markdown → Confluence)
  - scripts/cf2md.py (Confluence → Markdown)
  - Using md2cf library (Python)
  - Using html2text or confluence-to-markdown-converter

Authentication:
  - MCP: OAuth 2.1 (official)
  - Scripts: API Token (environment variables)
  - Both can coexist (no conflict)
```

### Why This Configuration?

1. **OAuth for MCP**: Best user experience, suitable for interactive operations
2. **API Token for Scripts**: Suitable for automation scripts, CI/CD
3. **Both authentications coexist**:
   - MCP for search, listing, metadata operations (requires interaction)
   - Scripts for batch processing, content conversion (requires stability)
4. **Storage Format**: More mature than ADF, better conversion quality
5. **Python-based**: Fits existing ecosystem, simple dependency management

---

## 10. Performance Analysis: MCP Roundtrip vs REST API Direct

### Real-World Performance Test (2026-01-23)

**Task**: Add a single table row to Confluence page (structural modification)

| Method | Total Time | Breakdown | Bottleneck |
|--------|-----------|-----------|-----------|
| **MCP Roundtrip (via Claude)** | ~13 minutes | • MCP Read: 17s<br>• **AI Tool Delays: ~12 min**<br>• Python Processing: 10s<br>• MCP Write: 43s | ⚠️ AI tool invocation intervals |
| **Python REST API Direct** | ~10-20 seconds | • REST API Read: 5-10s<br>• Python Processing: <1s<br>• REST API Write: 5-10s | ✅ Network I/O only |

### Root Cause Analysis

#### ❌ The Real Bottleneck: AI Tool Invocation Delays

When using MCP through Claude Code, the bottleneck is **NOT** the MCP server itself, but the **AI processing between
tool calls**:

```
Timeline of MCP Roundtrip Operation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

21:24:12  MCP Read completes (returns 77KB JSON)
          ↓
          [4m49s delay] ← AI processes JSON + prepares heredoc
          ↓
21:29:01  Bash: Write JSON to file via heredoc (actual: 0.003s)
          ↓
          [25s delay] ← AI prepares next command
          ↓
21:29:27  Bash: Run Python script
          ↓
          [10s execution] ← Python actual processing time
          ↓
21:29:37  Python completes
          ↓
          [18s delay] ← AI prepares grep command
          ↓
21:29:54  Bash: grep and prepare JSON
          ↓
          [6m20s delay] ← AI prepares Read + MCP Write
          ↓
21:36:14  MCP Write begins
          ↓
          [43s network I/O] ← MCP Write execution
          ↓
21:36:57  Complete

Total: ~13 minutes (782 seconds)
Actual tool execution: ~70 seconds (9%)
AI processing delays: ~712 seconds (91%)
```

#### Why AI Tool Delays Happen

1. **Large JSON Processing**
   - MCP returns 77KB JSON → AI needs to parse and understand structure
   - Preparing 30KB heredoc → AI generates every character token-by-token
   - Each tool call requires full context processing

2. **Multiple Tool Invocations**

   ```
   MCP Read (77KB output)
     → Claude processes
     → Bash heredoc (30KB input)    ← Token generation
     → Claude processes
     → Python execution
     → Claude processes
     → Read tool (30KB output)
     → Claude processes
     → MCP Write (30KB input)       ← Token generation
   ```

3. **Token Generation Cost**
   - Generating large heredoc strings is slow (character by character)
   - Each arrow (→) represents minutes of AI "thinking time"

#### ✅ Why Python REST API Direct is Fast

**Single Python script eliminates all AI involvement:**

```python
#!/usr/bin/env python3
import requests
import json
import os

# All operations happen in Python, no AI delays
api_url = os.environ['CONFLUENCE_URL']
auth = (os.environ['CONFLUENCE_USER'], os.environ['CONFLUENCE_API_TOKEN'])

# 1. Read page (5-10s - network only)
response = requests.get(f"{api_url}/rest/api/v2/pages/{page_id}")
page_data = response.json()

# 2. Modify JSON (<1s - pure Python)
# Find table, insert row
page_data['body']['storage']['value'] = modified_html

# 3. Write back (5-10s - network only)
requests.put(f"{api_url}/rest/api/v2/pages/{page_id}", json=page_data)

# Total: 10-20 seconds
```

### When to Use Each Method

| Scenario | Use MCP Roundtrip | Use Python REST API |
|----------|------------------|-------------------|
| **Interactive exploration** | ✅ Good | ❌ Requires scripting |
| **Simple text edits** | ✅ Acceptable | ⚠️ Overkill |
| **Structural changes** (add rows, modify tables) | ❌ Too slow | ✅ Fast & direct |
| **Batch operations** | ❌ Too slow | ✅ Efficient |
| **Automation/CI-CD** | ❌ Not suitable | ✅ Perfect |
| **One-off operations** | ⚠️ Slow but acceptable | ✅ Better |
| **Repeated operations** | ❌ Prohibitively slow | ✅ Must use |

### Optimization Strategies

#### For MCP Roundtrip (if you must use it)

1. **Use pipe instead of intermediate files**

   ```bash
   # BAD (requires AI to generate large heredoc):
   cat > file.json << 'EOF'
   {...huge JSON...}
   EOF

   # BETTER (less AI token generation):
   mcp_read | python script.py | mcp_write
   ```

2. **Minimize tool invocations**
   - Each tool boundary = minutes of AI delay
   - Combine operations in single tool when possible

3. **Keep data small**
   - Large JSON = longer AI processing
   - Consider filtering data before passing between tools

#### For Python REST API (recommended)

1. **Use environment variables** (already configured):

   ```python
   CONFLUENCE_URL = os.environ.get('CONFLUENCE_URL')
   CONFLUENCE_USER = os.environ.get('CONFLUENCE_USER')
   CONFLUENCE_API_TOKEN = os.environ.get('CONFLUENCE_API_TOKEN')
   ```

2. **Add error handling and retry logic**

   ```python
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry

   session = requests.Session()
   retry = Retry(total=3, backoff_factor=1)
   session.mount('https://', HTTPAdapter(max_retries=retry))
   ```

3. **Use ADF format for structural modifications**
   - Storage Format requires HTML parsing
   - ADF is JSON-native (easier to manipulate)

### Conclusion

**For structural modifications** (adding table rows, modifying layouts):

- MCP Roundtrip: **13 minutes** (due to AI tool delays)
- Python REST API: **10-20 seconds** (network only)
- **Speedup: 40-80x faster**

**Key Insight**: The bottleneck is not MCP itself (network operations are only ~60 seconds), but the AI tool invocation
intervals (~12 minutes). For any operation requiring precise structural modifications, use Python REST API directly.

**Recommendation**:

- Use MCP for interactive exploration and simple edits
- Use Python REST API for structural modifications and automation
- Keep credentials in environment variables (they can coexist)

---

## References

- [Official Atlassian MCP](https://github.com/atlassian/atlassian-mcp-server)
- [Ivan Dachev's Guide](https://ivandachev.com/blog/claude-code-mcp-atlassian-integration)
- [Markdown Confluence Tools](https://markdown-confluence.com/)
- [md2cf Documentation](https://pypi.org/project/md2cf/)
- [atlas-doc-parser](https://atlas-doc-parser.readthedocs.io/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
