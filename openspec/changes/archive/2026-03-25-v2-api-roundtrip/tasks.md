## 1. ADF to Markdown Converter

- [x] 1.1 Create `adf_to_markdown.py` with recursive ADF tree walker skeleton and doc/paragraph/heading support
- [x] 1.2 Add text marks handling (strong, em, code, link, strike, underline)
- [x] 1.3 Add list support (bulletList, orderedList with nesting)
- [x] 1.4 Add codeBlock, blockquote, rule, and table conversion
- [x] 1.5 Add expand marker output (`<!-- EXPAND: "title" -->` with breakout attrs)
- [x] 1.6 Add panel marker output (`<!-- PANEL: type -->`)
- [x] 1.7 Add inline element markers (emoji `:name:`, mention `<!-- MENTION -->`, inlineCard `<!-- CARD -->`, status `<!-- STATUS -->`, date `<!-- DATE -->`)
- [x] 1.8 Add media/mediaSingle conversion to `![alt](filename)`
- [x] 1.9 Add unknown node type pass-through (`<!-- ADF:type {...} -->`)
- [x] 1.10 Add hardBreak and nested structure support

## 2. Markdown to ADF Converter

- [x] 2.1 Create `markdown_to_adf.py` with mistune-based `ADFRenderer` skeleton that outputs ADF JSON for paragraph and heading
- [x] 2.2 Add inline formatting to ADF marks (strong, em, code, link, strike)
- [x] 2.3 Add list, codeBlock, blockquote, rule, and table ADF output
- [x] 2.4 Add pre-processor to extract expand/panel block markers before mistune parsing
- [x] 2.5 Add expand marker parsing → ADF expand nodes (with breakout mark restoration)
- [x] 2.6 Add panel marker parsing → ADF panel nodes
- [x] 2.7 Add inline marker parsing (emoji `:name:` → ADF emoji, `<!-- MENTION -->` → ADF mention, `<!-- CARD -->` → ADF inlineCard, `<!-- STATUS -->` → ADF status, `<!-- DATE -->` → ADF date)
- [x] 2.8 Add unknown node type marker restoration (`<!-- ADF:type -->` → original node)
- [x] 2.9 Add localId generation for ADF nodes that require it
- [x] 2.10 Add marker-free markdown detection (backward compat: no markers → standard ADF output)

## 3. Update Download Script

- [x] 3.1 Modify `download_confluence.py` to use v2 API via `get_page_adf()` from `confluence_adf_utils.py`
- [x] 3.2 Replace `convert_storage_to_markdown()` with `adf_to_markdown()` call
- [x] 3.3 Add `--legacy` flag to preserve old v1 Storage format behavior
- [x] 3.4 Update frontmatter generation with v2 API metadata

## 4. Update Upload Script

- [x] 4.1 Modify `upload_confluence.py` to detect custom markers in markdown content
- [x] 4.2 Add ADF upload path: marker-detected → `markdown_to_adf()` → `update_page_adf()` via v2 API
- [x] 4.3 Keep Storage format path as fallback for marker-free markdown
- [x] 4.4 Add `--legacy` flag to force v1 Storage format behavior
- [x] 4.5 Add ADF-based page creation via v2 API (for `--space` mode)

## 5. Testing and Validation

- [x] 5.1 Test ADF→MD conversion using real ADF from page 2321482360 (has expand, emoji, mention, inlineCard, panel)
- [x] 5.2 Test MD→ADF conversion of the generated markdown back to ADF
- [x] 5.3 Verify roundtrip fidelity: compare original ADF vs roundtripped ADF for all element types
- [x] 5.4 Test backward compatibility: upload old-style markdown (no markers) still works via Storage format
- [x] 5.5 Test `--legacy` flag on both download and upload
- [x] 5.6 Test nested structures (panel inside expand, list inside panel)

## 6. Bug Fix and Documentation

- [x] 6.1 Commit `add_panel.py` fix for `\n` escape sequence handling
- [x] 6.2 Update SKILL.md to document new marker syntax and v2 API usage
- [x] 6.3 Update `roundtrip-implementation-comparison.md` Method 7 section with final implementation details
