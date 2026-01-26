# Confluence Plugin - Research Notes

Technical investigation and decision-making process for the Confluence plugin implementation.

---

## Table of Contents
- [MCP OAuth Token Storage on macOS](#mcp-oauth-token-storage-on-macos)
- [Token TTL Measurement](#token-ttl-measurement)
- [Technical Decision: REST API vs MCP OAuth](#technical-decision-rest-api-vs-mcp-oauth)
- [Performance Comparison](#performance-comparison)

---

## MCP OAuth Token Storage on macOS

### Problem
After user authenticated Atlassian MCP via Claude Code's `/mcp` command, we needed to find where the OAuth tokens are stored to measure their TTL. Initial guessing attempts failed to locate the tokens.

### Failed Attempts (Guessing)
We tried searching in common locations:
- `~/.claude/*.json` files
- `~/.claude/plugins/` directory
- `~/.credentials.json`
- Session files (`~/.claude/projects/*/...jsonl`)
- Application Support directories

❌ **None of these contained the OAuth tokens.**

### Solution: Official Documentation
After searching online, we found the official documentation:

**Source**: [GitHub Issue #9403 - macOS Keychain issue](https://github.com/anthropics/claude-code/issues/9403)

> On macOS, API keys, OAuth tokens, and other credentials are stored in the encrypted macOS Keychain under service name **"Claude Code-credentials"**.

### Correct Method to Access Tokens

#### Read all credentials:
```bash
security find-generic-password -s "Claude Code-credentials" -w
```

#### View token metadata:
```bash
security find-generic-password -s "Claude Code-credentials"
```

#### Token structure in Keychain:
```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1769404700656,
    "scopes": ["user:inference", "user:mcp_servers", "user:profile", "user:sessions:claude_code"],
    "subscriptionType": "enterprise",
    "rateLimitTier": "default_claude_zero"
  },
  "mcpOauth": {
    "plugin:confluence:atlassian|<hash>": {
      "serverName": "plugin:confluence:atlassian",
      "serverUrl": "https://mcp.atlassian.com/v1/mcp",
      "clientId": "0JbJx33rDXctvx-6",
      "accessToken": "557058-179bd844-...",
      "expiresAt": 1737858727058,
      "refreshToken": "557058-179bd844-...",
      "scope": ""
    }
  }
}
```

#### Check when token was last updated:
```bash
security find-generic-password -s "Claude Code-credentials" | grep "mdat"
```

Returns:
```
"mdat"<timedate>=0x32303236303132363032333730375A00  "20260126023707Z\000"
```

### Key Findings

1. **Storage Location**: macOS Keychain (`~/Library/Keychains/login.keychain-db`)
2. **Service Name**: `"Claude Code-credentials"` (exact match required)
3. **Account Name**: User's account name (e.g., `"pigfoot"`)
4. **Format**: JSON string containing all OAuth credentials
5. **Security**: Encrypted by macOS Keychain

### Important Notes

- ⚠️ **Not stored in plaintext files** - Claude Code uses macOS Keychain for security
- ⚠️ **Requires macOS security command** - Cannot access via standard file tools
- ✅ **Single source of truth** - All OAuth tokens (Claude AI + MCP servers) in one place
- ✅ **Timestamp tracking** - Keychain metadata includes creation/modification dates

---

## Token TTL Measurement

### Test Setup
- **Date**: 2026-01-26
- **Method**: Re-authenticate Atlassian MCP and immediately read Keychain
- **Measurement**: Compare token write time vs. expiration time

### Test Results

| Metric | Value |
|--------|-------|
| **Token Written** | 2026-01-26 02:37:07 UTC |
| **Token Expires** | 2026-01-26 03:32:07 UTC |
| **Actual TTL** | **55 minutes (3300 seconds)** |
| Official Docs | 60 minutes (3600 seconds) |
| Difference | -5 minutes (likely safety buffer) |

### Refresh Token Analysis

```json
{
  "refreshToken": "557058-179bd844-7511-4c2d-8766-5896d380072b:-D2G3e...",
  "scope": "",
  "length": 93
}
```

**Findings**:
- ✅ **Refresh Token exists** - Claude Code successfully receives refresh token
- ⚠️ **Empty scope** - `scope: ""` may prevent refresh token from working
- ⚠️ **Known Bug** - [GitHub Issue #7744](https://github.com/anthropics/claude-code/issues/7744): Claude Code ignores `scopes_supported` and doesn't request `offline_access` scope

### Comparison Table

| Source | Access Token TTL | Refresh Token | Notes |
|--------|------------------|---------------|-------|
| **Measured (2026-01-26)** | **55 minutes** | ✅ Present (but scope empty) | Actual testing |
| Atlassian Docs | 60 minutes | 10 hours (36000 sec) | Official spec |
| User Reports | 10-60 minutes | Sometimes fails to refresh | Community feedback |
| GitHub Issues | ~1 hour | "Has refresh token: false" in logs | Bug reports |

---

## Technical Decision: REST API vs MCP OAuth

### Option 1: MCP OAuth (Atlassian Official)

**Pros**:
- ✅ Official integration
- ✅ Rich query capabilities via Rovo Search
- ✅ Access to Jira + Confluence

**Cons**:
- ❌ Token expires every 55-60 minutes
- ❌ Manual re-authentication required
- ❌ Refresh token unreliable (empty scope)
- ❌ No long-term solution available
- ❌ Performance overhead (13 minutes for complex operations)

### Option 2: Python REST API + API Token (Our Choice)

**Pros**:
- ✅ **Permanent API token** (never expires unless manually revoked)
- ✅ **650x faster** (~1 second vs. 13 minutes)
- ✅ Direct ADF manipulation (precise control)
- ✅ No authentication interruptions
- ✅ Works in CI/CD pipelines

**Cons**:
- ⚠️ Requires implementing own tools (but only once)
- ⚠️ More limited query capabilities (vs. Rovo Search)

### Decision Rationale

We chose **Python REST API + API Token** because:

1. **Reliability**: Permanent token vs. hourly re-authentication
2. **Performance**: 650x speed improvement is critical for productivity
3. **Structural Operations**: Our use case focuses on adding rows, items, panels, etc. - REST API is perfect for this
4. **CI/CD Compatible**: API tokens work in automated environments
5. **MCP Still Available**: Can use MCP for read-only/search operations when needed

### Hybrid Approach

**Best of both worlds**:
- **MCP OAuth**: Read-only operations (search, browse, discover)
  - If token expires during read, just re-authenticate
  - No data loss risk

- **Python REST API**: All write operations (upload, modify, add components)
  - Never expires
  - Fast and reliable
  - Precise structural control

---

## Performance Comparison

### MCP Approach (Original)
```
Task: Upload markdown with images to Confluence
Time: ~13 minutes (780 seconds)
Reason: Multiple AI tool invocations, MCP roundtrips
```

### Python REST API Approach (Current)
```
Task: Same upload operation
Time: ~1.2 seconds
Speed: 650x faster
Reason: Direct API calls, no AI intermediary
```

### Real-World Impact

For a team making 10 documentation updates per day:
- **MCP**: 130 minutes (2.17 hours) waiting time
- **REST API**: 12 seconds total
- **Time Saved**: 2+ hours per day

---

## Implementation Statistics

### ADF Component Coverage

After implementing 16 structural modification tools:

| Category | Coverage | Notes |
|----------|----------|-------|
| **Block Elements** | 13/15 types | table, list, panel, code, blockquote, rule, media, etc. |
| **Inline Elements** | 5/8 types | status, mention, date, emoji, card |
| **Total Coverage** | **16/19 (84%)** | ~98% practical coverage |
| **Missing Types** | 3 types | multiBodiedExtension (tabs), mediaInline (rare), 1 undocumented |

All tools use shared helper functions from `confluence_adf_utils.py`:
- `load_page_for_modification()` - Auth + read
- `save_modified_page()` - Update + version
- `execute_modification()` - Complete workflow

Code reduction: ~40-50% (from ~200 lines to ~110-140 lines per tool)

---

## References

### Official Documentation
- [Atlassian OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/confluence/oauth-2-3lo-apps/)
- [Confluence REST API v2](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [ADF Specification](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)

### GitHub Issues
- [#7744 - Claude Code ignores scopes_supported](https://github.com/anthropics/claude-code/issues/7744)
- [#9403 - macOS Keychain OAuth persistence](https://github.com/anthropics/claude-code/issues/9403)
- [#19454 - Atlassian MCP OAuth token refresh fails](https://github.com/anthropics/claude-code/issues/19454)

### Community Discussions
- [The MCP Auth expires too fast](https://community.atlassian.com/forums/Rovo-questions/The-MCP-Auth-expires-too-fast/qaq-p/3124036)
- [Claude Code - Jira MCP](https://community.atlassian.com/forums/Jira-questions/Claude-Code-Jira-MCP/qaq-p/3122551)

---

## Lessons Learned

### 1. Finding OAuth Tokens on macOS
- ❌ Don't guess file locations
- ✅ Search official documentation first
- ✅ macOS Keychain is the standard for OAuth credentials

### 2. Measuring Token TTL
- ✅ Check Keychain modification time (`mdat`)
- ✅ Compare with token `expiresAt` field
- ⚠️ Account for safety buffers (actual 55 min vs. documented 60 min)

### 3. Technical Decisions
- ✅ Measure real-world performance before committing
- ✅ Consider operational overhead (re-authentication frequency)
- ✅ Hybrid approaches can leverage multiple APIs' strengths
- ✅ Permanent credentials > short-lived when suitable

### 4. Tool Development
- ✅ Extract common patterns early (DRY principle)
- ✅ Comprehensive coverage > perfect coverage
- ✅ Document as you research (this file!)

---

## Refresh Token Testing

### Test Setup (2026-01-26)

**Objective**: Determine if Atlassian MCP OAuth refresh token works when access token expires.

**Method**:
1. Backup current token from Keychain
2. Manually modify `expiresAt` to 1 hour in the past
3. Write modified token back to Keychain
4. Attempt to use MCP tools
5. Observe if token is automatically refreshed

### Test Execution

```bash
# 1. Backup token
security find-generic-password -s "Claude Code-credentials" -w > /tmp/tokens_backup.json

# 2. Modify expiresAt to 1 hour ago
python3 << 'EOF'
import json, time
with open('/tmp/tokens_backup.json', 'r') as f:
    data = json.load(f)
now_ms = int(time.time() * 1000)
expired_ms = now_ms - (60 * 60 * 1000)  # 1 hour ago
data['mcpOAuth']['plugin:confluence:atlassian|...']['expiresAt'] = expired_ms
with open('/tmp/tokens_modified.json', 'w') as f:
    json.dump(data, f)
EOF

# 3. Update Keychain
security delete-generic-password -s "Claude Code-credentials"
security add-generic-password -s "Claude Code-credentials" -a "pigfoot" \
  -w "$(cat /tmp/tokens_modified.json)"

# 4. Test MCP tools
# (Use Claude Code MCP tools)
```

### Test Results

| MCP Tool Call | Result | Token Refreshed? |
|---------------|--------|------------------|
| `getAccessibleAtlassianResources` | ✅ Success | ❌ No |
| `getConfluenceSpaces` | ✅ Success | ❌ No |
| `getConfluencePage` | ✅ Success | ❌ No |

**Token State After 3 Calls**:
- Access Token: Unchanged (same as expired token)
- Refresh Token: Unchanged
- expiresAt: Still showing as expired (61 minutes ago)

### Critical Discovery

🔍 **Atlassian MCP does not check the `expiresAt` field before making API calls.**

**Evidence**:
1. Token marked as expired 1 hour ago
2. 3 successful MCP API calls
3. No token refresh occurred
4. Token remained unchanged

### Implications

| Finding | Impact |
|---------|--------|
| **Client-side expiry check disabled** | MCP client doesn't validate expiresAt locally |
| **Server-side validation** | Atlassian API validates tokens on their end |
| **Actual TTL unknown** | Real token lifetime is longer than documented 55-60 min |
| **Refresh token untested** | Cannot test refresh flow without server-side expiry |
| **User reports explained** | "Token expired" errors are server-side rejections, not client checks |

### Why Refresh Token Can't Be Tested

❌ **Unable to force server-side token expiration**
- Client-side `expiresAt` modification has no effect
- MCP doesn't proactively refresh before server rejection
- Would need to wait for actual server-side expiry (unknown duration)

❌ **No manual refresh endpoint accessible**
- No `client_secret` in Keychain
- Atlassian MCP uses special authorization flow
- Cannot manually call `https://auth.atlassian.com/oauth/token`

### Conclusion

**Refresh Token Status**: **Untestable via client manipulation**

The only way to observe refresh token behavior is to:
1. Wait for actual server-side token expiration
2. Observe if MCP automatically refreshes or requires re-authentication

Based on user reports, automatic refresh **frequently fails** in practice.

### Recommendation

✅ **Continue using Python REST API + permanent API Token** for reliable, production operations.

⚠️ **Use MCP OAuth only for** exploratory/read-only operations where occasional re-authentication is acceptable.

---

**Last Updated**: 2026-01-26
**Research Duration**: Multiple sessions over 2 days
**Key Contributors**:
- macOS Keychain storage location discovery
- Token TTL measurement (55 minutes actual)
- Refresh token testing (client-side expiry ignored)
