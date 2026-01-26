#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mistune>=3.0.0",
# ]
# ///
"""
Convert Markdown to Confluence Wiki Markup

Usage:
    uv run convert_markdown_to_wiki.py input.md output.wiki
    uv run convert_markdown_to_wiki.py input.md  # outputs to stdout

Wiki Markup Quick Reference:
    Markdown          Wiki Markup
    # H1              h1. H1
    ## H2             h2. H2
    **bold**          *bold*
    *italic*          _italic_
    `code`            {{code}}
    [text](url)       [text|url]
    - item            * item
    1. item           # item
"""

import sys
import argparse
import re
from typing import Optional

import mistune


class WikiMarkupRenderer(mistune.BaseRenderer):
    """Renderer that outputs Confluence Wiki Markup."""

    NAME = 'wiki'

    def text(self, token, state):
        return token['raw']

    def block_text(self, token, state):
        """Render block-level text (used in list items)."""
        return self.render_tokens(token['children'], state)

    def paragraph(self, token, state):
        text = self.render_tokens(token['children'], state)
        return f'{text}\n\n'

    def heading(self, token, state):
        text = self.render_tokens(token['children'], state)
        level = token['attrs']['level']
        return f'h{level}. {text}\n\n'

    def emphasis(self, token, state):
        text = self.render_tokens(token['children'], state)
        return f'_{text}_'

    def strong(self, token, state):
        text = self.render_tokens(token['children'], state)
        return f'*{text}*'

    def codespan(self, token, state):
        text = token['raw']
        return f'{{{{{text}}}}}'

    def link(self, token, state):
        text = self.render_tokens(token['children'], state)
        url = token['attrs']['url']
        if text == url:
            return f'[{url}]'
        return f'[{text}|{url}]'

    def image(self, token, state):
        url = token['attrs']['url']
        return f'!{url}!'

    def block_code(self, token, state):
        code = token['raw']
        info = token.get('attrs', {}).get('info', '')
        if info:
            return f'{{code:language={info}}}\n{code}{{code}}\n\n'
        return f'{{code}}\n{code}{{code}}\n\n'

    def block_quote(self, token, state):
        text = self.render_tokens(token['children'], state)
        lines = text.strip().split('\n')
        quoted = '\n'.join(f'bq. {line}' for line in lines)
        return f'{quoted}\n\n'

    def list(self, token, state):
        body = self.render_tokens(token['children'], state)
        return body + '\n'

    def list_item(self, token, state):
        text = self.render_tokens(token['children'], state)
        # Determine if ordered from parent list
        ordered = token.get('attrs', {}).get('ordered', False)
        marker = '#' if ordered else '*'
        return f'{marker} {text.strip()}\n'

    def newline(self, token, state):
        return '\n'

    def blank_line(self, token, state):
        return '\n'

    def linebreak(self, token, state):
        return '\\\\\n'

    def thematic_break(self, token, state):
        return '----\n\n'

    def strikethrough(self, token, state):
        text = self.render_tokens(token['children'], state)
        return f'-{text}-'

    def table(self, token, state):
        text = self.render_tokens(token['children'], state)
        return f'{text}\n'

    def table_head(self, token, state):
        text = self.render_tokens(token['children'], state)
        return text

    def table_body(self, token, state):
        text = self.render_tokens(token['children'], state)
        return text

    def table_row(self, token, state):
        text = self.render_tokens(token['children'], state)
        return f'{text}\n'

    def table_cell(self, token, state):
        text = self.render_tokens(token['children'], state)
        is_head = token.get('attrs', {}).get('head', False)
        if is_head:
            return f'||{text}'
        return f'|{text}'


def convert_markdown_to_wiki(markdown_text: str) -> str:
    """Convert Markdown text to Confluence Wiki Markup."""
    
    renderer = WikiMarkupRenderer()
    parser = mistune.create_markdown(renderer=renderer)
    wiki_markup = parser(markdown_text)
    
    # Post-processing cleanup
    wiki_markup = re.sub(r'\n{3,}', '\n\n', wiki_markup)  # Remove excessive newlines
    wiki_markup = wiki_markup.strip()
    
    return wiki_markup


def main():
    parser = argparse.ArgumentParser(
        description='Convert Markdown to Confluence Wiki Markup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s input.md output.wiki
    %(prog)s input.md  # outputs to stdout

Wiki Markup Conversion:
    # H1           → h1. H1
    ## H2          → h2. H2
    **bold**       → *bold*
    *italic*       → _italic_
    `code`         → {{code}}
    [text](url)    → [text|url]
    - item         → * item
    1. item        → # item
        """
    )
    
    parser.add_argument('input', type=str, help='Input Markdown file')
    parser.add_argument('output', type=str, nargs='?', help='Output Wiki file (stdout if omitted)')
    
    args = parser.parse_args()
    
    # Read input
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert
    wiki_markup = convert_markdown_to_wiki(markdown_text)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(wiki_markup)
        print(f"✅ Converted: {args.input} → {args.output}")
    else:
        print(wiki_markup)


if __name__ == '__main__':
    main()
