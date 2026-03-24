# 007 - Confluence Attachment Upload

Fix media ID handling and add general-purpose attachment upload support.

## Documents

- [research.md](research.md) - API investigation, experiments, and findings
- OpenSpec change: `openspec/changes/confluence-attachment-upload/`

## Summary

- `add_media.py` / `add_media_group.py` use wrong ID (`attachment ID` vs `fileId`) causing "Preview unavailable"
- Storage format (`upload_confluence.py`) works fine — no change needed
- New `upload_attachment.py` script for any file type with mediaSingle/mediaGroup display
