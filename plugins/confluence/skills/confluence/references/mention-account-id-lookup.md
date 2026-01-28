# Getting Confluence Account IDs for @mentions

**Version**: 0.1.0
**Last Updated**: 2026-01-27

## Overview

To add @mentions in Confluence using `add_mention.py`, you need the user's Confluence account ID in the format:

```
557058:179bd844-7511-4c2d-8766-5896d380072b
```

This reference documents tested methods for obtaining account IDs.

## Quick Reference

| Method | Success Rate | Speed | Notes |
|--------|--------------|-------|-------|
| Jira API lookup | ✅ High | Fast | Works if user has Jira access |
| Page metadata | ✅ High | Fast | Get from pages they **created** |
| Personal space | ✅ High | Fast | Get from their personal space |
| Existing @mention | ✅ 100% | Medium | Extract from pages they're **mentioned in** |
| CQL search | ❌ Low | Fast | Often returns 0 results |
| Email lookup | ❌ N/A | N/A | Blocked by GDPR |

---

## ✅ Method 1: Jira API User Lookup (RECOMMENDED)

**When to use**: When you know the user's name or email

**Requirements**:

- Jira access (via MCP OAuth)
- User must exist in Jira

**Success rate**: High (works for most users)

**Tested with**: User A ✅, User B ✅

### Steps

1. Ensure Jira MCP access (run `/mcp` if needed)

2. Use `lookupJiraAccountId`:

   ```python
   # Via MCP tool
   mcp__plugin_confluence_atlassian__lookupJiraAccountId(
       cloudId="79a3ee80-0d14-4a82-9335-03f989902e7a",
       searchString="User A"  # or email
   )
   ```

3. Result:

   ```json
   {
     "accountId": "557058:179bd844-7511-4c2d-8766-5896d380072b",
     "displayName": "User A",
     "html": "<strong>User A</strong> - user.a@company.com"
   }
   ```

**Limitations**:

- Requires valid Jira OAuth token
- User must have Jira access

**Note**: May return different account ID formats depending on when the account was created:

- Old accounts: `622a2d144160640069caec19` (hex string only)
- New accounts: `557058:179bd844-7511-4c2d-8766-5896d380072b` (number:UUID)
- **Both formats work correctly in Confluence @mentions**

---

## ✅ Method 2: Page Metadata (RELIABLE)

**When to use**: When you need to find the **page author's** account ID

**Key difference**: Gets account ID from **pages the user created/owns**, not pages where they're mentioned.

**Requirements**:

- Know at least one page ID created by the user
- Confluence MCP access

**Success rate**: 100% (if page exists)

**Tested with**: User A ✅, User B ✅

### Steps

1. Find a page **created by the user**:
   - Search: `mcp__plugin_confluence_atlassian__search(query="User B author")`
   - Or if you already know a specific page ID they created

2. Get page metadata (no need to read full body):

   ```python
   mcp__plugin_confluence_atlassian__getConfluencePage(
       cloudId="79a3ee80-0d14-4a82-9335-03f989902e7a",
       pageId="746336757"
       # Don't need contentFormat="adf" - metadata is enough
   )
   ```

3. Extract from response:

   ```json
   {
     "authorId": "622a2d144160640069caec19",
     "ownerId": "622a2d144160640069caec19"
   }
   ```

**Use `authorId` or `ownerId`** - both contain the account ID.

**Advantage**: Faster than Method 4 (no need to parse full page body and find mention nodes).

---

## ✅ Method 3: Personal Space Lookup

**When to use**: When you can guess the user's personal space URL

**Requirements**:

- User has a personal Confluence space
- Confluence MCP access

**Success rate**: High (if personal space exists)

**Tested with**: User A ✅

### Steps

1. Find user's personal space:
   - Manual: Navigate to their profile in Confluence
   - Or try space key format: `~{accountIdWithoutColons}`
   - Example: `~557058179bd84475114c2d87665896d380072b`

2. Get space metadata:

   ```python
   mcp__plugin_confluence_atlassian__getConfluenceSpaces(
       cloudId="79a3ee80-0d14-4a82-9335-03f989902e7a",
       keys="~557058179bd84475114c2d87665896d380072b"
   )
   ```

3. Extract from response:

   ```json
   {
     "spaceOwnerId": "557058:179bd844-7511-4c2d-8766-5896d380072b",
     "authorId": "557058:179bd844-7511-4c2d-8766-5896d380072b"
   }
   ```

**Limitations**: Requires knowing the space key format first.

---

## ✅ Method 4: Extract from Existing @mention (MOST RELIABLE)

**When to use**: When you need to find account ID from **pages where the user is @mentioned**

**Key difference**: Gets account ID from **pages mentioning the user**, not necessarily pages they created. This is the
GOLD STANDARD - the format is guaranteed to work in Confluence.

**Requirements**:

- Know a page with existing @mention of the user
- Confluence MCP access

**Success rate**: 100%

**Tested with**: User A ✅, User B ✅

**Use cases**:

- User doesn't create many pages (harder to use Method 2)
- You want to verify the exact format used in Confluence
- User is frequently mentioned by others

### Steps

1. Search for pages containing the user's name:

   ```python
   mcp__plugin_confluence_atlassian__search(
       query="User A @mention"
   )
   ```

2. Read page in ADF format:

   ```python
   mcp__plugin_confluence_atlassian__getConfluencePage(
       cloudId="79a3ee80-0d14-4a82-9335-03f989902e7a",
       pageId="2130805210",
       contentFormat="adf"
   )
   ```

3. Find mention node in ADF:

   ```json
   {
     "type": "mention",
     "attrs": {
       "id": "557058:179bd844-7511-4c2d-8766-5896d380072b",
       "text": "@User A"
     }
   }
   ```

4. Extract `attrs.id` - this is the account ID.

**This is the GOLD STANDARD** - the format is guaranteed to work in Confluence.

---

## 🔄 Method 2 vs Method 4: When to Use Which?

| Aspect | Method 2: Page Metadata | Method 4: ADF Mention |
|--------|------------------------|----------------------|
| **Source** | Pages **created by** user | Pages **mentioning** user |
| **Data read** | Metadata only (lightweight) | Full ADF body (heavier) |
| **Speed** | Faster | Slower |
| **Reliability** | 100% if user created pages | 100% if user was mentioned |
| **Best for** | Active content creators | Users frequently mentioned by others |
| **Format guarantee** | ✅ Correct | ✅ GOLD STANDARD (definitely correct) |

**Quick decision**:

- Know a page they **created**? → Use Method 2
- Know a page they're **mentioned in**? → Use Method 4
- Both work? → Use Method 2 (faster)

---

## ❌ Method 5: CQL Search (NOT RECOMMENDED)

**When to use**: Don't use this method

**Tested with**: User A ❌

### What we tried

```python
# Both returned 0 results:
searchConfluenceUsingCql(cql='creator = "User A"')
searchConfluenceUsingCql(cql='contributor = "User A"')
```

**Why it fails**:

- CQL user fields may require account ID instead of display name
- Inconsistent behavior
- Not worth debugging

---

## ❌ Method 6: Email Lookup (NOT SUPPORTED)

**Status**: Blocked by API

**Reason**: GDPR and privacy regulations

Atlassian removed email-to-account-ID lookup from both Confluence and Jira APIs.

**Documentation**:

- [How can we get the user Account Id in confluence cloud via email
  id?](https://community.atlassian.com/forums/Confluence-questions/How-can-we-get-the-user-Account-Id-in-confluence-cloud-via-email/qaq-p/2911212)
- [REST API migration guide - removal of username and
  userkey](https://developer.atlassian.com/cloud/confluence/deprecation-notice-user-privacy-api-migration-guide/)

---

## Recommended Workflow

### Scenario A: You know their name/email

1. Use **Method 1 (Jira API lookup)**
2. Use the returned account ID directly (both old and new formats work)

### Scenario B: You know pages they created

1. Use **Method 2 (Page metadata)**
2. Extract `authorId` or `ownerId`

### Scenario C: You're unsure

1. Use **Method 4 (Existing @mention)** - most reliable
2. Search for pages containing their name
3. Read page in ADF format
4. Extract from mention node

---

## Account ID Format Reference

### New Format (Post-2020 accounts)

```
557058:179bd844-7511-4c2d-8766-5896d380072b
```

- Structure: `{number}:{UUID}`
- Format: `\d+:[a-f0-9-]{36}`
- Used for accounts created after Atlassian ID system update

### Old Format (Pre-2020 accounts)

```
622a2d144160640069caec19
```

- Structure: Hex string only
- Format: `[a-f0-9]+`
- Used for accounts created before Atlassian ID system update

**Both formats are valid and work correctly in Confluence @mentions.**

---

## Troubleshooting

### "401 Unauthorized" when using MCP tools

**Cause**: OAuth token expired

**Fix**: Run `/mcp` and re-authenticate

See [troubleshooting.md](troubleshooting.md) for details.

### Jira API returns different format

**Not a Problem**: Account ID like `622a2d144160640069caec19` (old format) vs `557058:179bd...` (new format)

**Why**: Different formats for accounts created at different times

**Solution**: Both formats work correctly - use the ID returned by Jira API directly.

### Can't find user in Jira

**Problem**: `lookupJiraAccountId` returns no results

**Reasons**:

- User doesn't have Jira access
- User only has Confluence access
- Name spelling is different

**Solution**: Use **Method 2** or **Method 4** instead.

---

## Test Results Summary

### Test Subject 1: User A (New Format Account)

**Correct Account ID**: `557058:179bd844-7511-4c2d-8766-5896d380072b`

| Method | Result | Account ID Found |
|--------|--------|------------------|
| Jira API lookup | ✅ Success | `557058:179bd844-7511-4c2d-8766-5896d380072b` |
| Page metadata (authorId) | ✅ Success | `557058:179bd844-7511-4c2d-8766-5896d380072b` |
| Page metadata (ownerId) | ✅ Success | `557058:179bd844-7511-4c2d-8766-5896d380072b` |
| Personal space | ✅ Success | `557058:179bd844-7511-4c2d-8766-5896d380072b` |
| ADF mention node | ✅ Success | `557058:179bd844-7511-4c2d-8766-5896d380072b` |
| CQL creator | ❌ Failed | 0 results |
| CQL contributor | ❌ Failed | 0 results |

### Test Subject 2: User B (Old Format Account)

**Correct Account ID**: `622a2d144160640069caec19`

| Method | Result | Account ID Found |
|--------|--------|------------------|
| Jira API lookup | ✅ Success | `622a2d144160640069caec19` |
| Page metadata (authorId) | ✅ Success | `622a2d144160640069caec19` |
| ADF mention node | ✅ Success | `622a2d144160640069caec19` |

**Verified**: Old format account ID works correctly in Confluence @mentions (page 2130805210)

---

## See Also

- [add_mention.py usage](../scripts/add_mention.py)
- [Troubleshooting guide](troubleshooting.md)
- [SKILL.md](../SKILL.md)
