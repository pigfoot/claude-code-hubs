## 1. Page Width Support

- [x] 1.1 Add `--width` CLI argument (choices: `full`/`narrow`, default `full`)
- [x] 1.2 Add frontmatter support for `confluence.width` field
- [x] 1.3 Pass `full_width=` parameter to `create_page()` and `update_page()` calls
- [x] 1.4 CLI `--width` takes precedence over frontmatter

## 2. Table Layout

- [x] 2.1 Add `table_layout` parameter to `ConfluenceStorageRenderer.__init__()`
- [x] 2.2 Modify `table()` method to render `<table data-layout="...">` using the parameter
- [x] 2.3 Add `--table-layout` CLI argument (choices: `full-width`/`default`, default `full-width`)
- [x] 2.4 Add frontmatter support for `confluence.table.layout` field

## 3. Column Width Support

- [x] 3.1 Add `colwidths` parameter to `ConfluenceStorageRenderer.__init__()`
- [x] 3.2 Track column count per table in renderer (count `<th>`/`<td>` in first row)
- [x] 3.3 Generate `<colgroup>` with proportional pixel `<col>` elements (1280px base) when colwidths match column count
- [x] 3.4 Skip `<colgroup>` and print warning when colwidths length mismatches column count
- [x] 3.5 Add frontmatter support for `confluence.table.colwidths` field (list of ratio values)

## 4. Testing

- [x] 4.1 Test on Confluence: page with `full_width=True` renders wide
- [x] 4.2 Test on Confluence: table with `data-layout="full-width"` + `<colgroup>` renders correct column proportions
- [x] 4.3 Test: `--width narrow` overrides default to narrow layout
- [x] 4.4 Test: table without colwidths renders with equal auto-distribution

## 5. Documentation

- [x] 5.1 Update SKILL.md: document `--width` and `--table-layout` flags, frontmatter options
- [x] 5.2 Update plugin README.md: add formatting capabilities section
