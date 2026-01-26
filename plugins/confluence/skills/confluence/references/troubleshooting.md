# Troubleshooting Guide

## Authentication Errors

### "Missing environment variables"

**Cause:** Required credentials not set.

**Fix:** Create `.env` file or export variables:
```bash
export CONFLUENCE_URL="https://company.atlassian.net/wiki"
export CONFLUENCE_USER="your-email@company.com"
export CONFLUENCE_API_TOKEN="your-api-token"
```

### "401 Unauthorized"

**Cause:** Invalid credentials or expired token.

**Fix:**
1. Verify email address is correct
2. Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens
3. Ensure token has Confluence access

### "403 Forbidden"

**Cause:** User lacks permission for the page/space.

**Fix:**
1. Check space permissions in Confluence
2. Request access from space admin
3. Verify page isn't restricted

## Upload Errors

### "Content too large" / MCP size limit

**Cause:** Using MCP for large uploads (>10-20KB).

**Fix:** Use the upload script instead:
```bash
uv run {base_dir}/scripts/upload_confluence.py document.md --id PAGE_ID
```

### "Page not found"

**Cause:** Invalid page ID or page was deleted.

**Fix:**
1. Verify page ID from URL: `.../pages/123456789/...`
2. Check page exists in Confluence
3. Ensure you have view permission

### "Version conflict"

**Cause:** Page was modified by someone else.

**Fix:**
1. Re-fetch current version
2. Merge changes manually
3. Re-upload with updated version

### Images not showing

**Cause:** Attachments not uploaded or wrong path.

**Fix:**
1. Ensure image files exist locally
2. Use relative paths: `![alt](./images/diagram.png)`
3. Verify attachments uploaded: check page attachments in Confluence
4. Don't use raw XML `<ac:image>` in markdown

## Download Errors

### "Page content empty"

**Cause:** Page uses unsupported macros.

**Fix:**
1. Check page in Confluence for custom macros
2. Manually extract content if needed
3. Some macros (like JIRA) won't convert

### Attachments not downloading

**Cause:** Network issue or permission problem.

**Fix:**
1. Check network connectivity
2. Verify you can download attachments manually
3. Check attachment permissions

## Conversion Errors

### Markdown formatting broken

**Cause:** Unsupported or nested formatting.

**Fix:**
1. Simplify complex nested structures
2. Use code blocks for preformatted text
3. Check for unescaped special characters

### Tables not rendering

**Cause:** Invalid table structure.

**Fix:**
1. Ensure header row has `||` separators
2. Data rows use `|` separators
3. No empty cells at row start/end

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using MCP for large uploads | Use `upload_confluence.py` script |
| Raw XML in markdown | Use markdown image syntax |
| Mermaid code blocks | Pre-convert to PNG/SVG |
| Wrong page ID | Get from URL: `/pages/{ID}/` |
| Expired API token | Generate new token |

## Debug Tips

1. **Always use `--dry-run` first** to preview changes
2. **Check page version** before updating
3. **Verify file paths** for images
4. **Test with small content** before large uploads
5. **Check Confluence directly** if something looks wrong
