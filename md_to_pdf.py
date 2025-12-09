#!/usr/bin/env python3
"""
Markdown to PDF Converter with Full Styling Control

Converts markdown CV to beautifully formatted PDF with customizable:
- Margins
- Fonts (family, size, colors)
- Spacing (line height, paragraph spacing)
- Colors (headings, text, accents)
"""

import markdown
from pathlib import Path
from typing import Dict, Optional
import json


class PDFStyleConfig:
    """Configuration for PDF styling"""

    DEFAULT_STYLE = {
        # Page settings
        "page": {
            "size": "A4",
            "margin_top": "2cm",
            "margin_bottom": "2cm",
            "margin_left": "2cm",
            "margin_right": "2cm",
        },

        # Font settings
        "fonts": {
            "body_family": "Calibri, Arial, sans-serif",
            "body_size": "10pt",
            "body_color": "#000000",
            "body_line_height": "1.4",

            "heading1_family": "Calibri, Arial, sans-serif",
            "heading1_size": "18pt",
            "heading1_color": "#000000",
            "heading1_weight": "bold",

            "heading2_family": "Calibri, Arial, sans-serif",
            "heading2_size": "12pt",
            "heading2_color": "#000000",
            "heading2_weight": "bold",

            "heading3_family": "Calibri, Arial, sans-serif",
            "heading3_size": "11pt",
            "heading3_color": "#000000",
            "heading3_weight": "bold",
        },

        # Spacing
        "spacing": {
            "paragraph_spacing": "0.3em",
            "heading1_margin_top": "0.5em",
            "heading1_margin_bottom": "0.3em",
            "heading2_margin_top": "0.8em",
            "heading2_margin_bottom": "0.4em",
            "heading3_margin_top": "0.6em",
            "heading3_margin_bottom": "0.3em",
            "list_spacing": "0.2em",
        },

        # Lists
        "lists": {
            "bullet_style": "disc",  # disc, circle, square, none
            "bullet_color": "#000000",
            "indent": "1.5em",
        },

        # Other elements
        "horizontal_rule": {
            "display": "block",
            "border": "none",
            "border_top": "1px solid #cccccc",
            "margin": "1em 0",
        },

        "bold": {
            "weight": "bold",
            "color": None,  # None = inherit from parent
        },
    }

    def __init__(self, custom_style: Dict = None):
        """Initialize with default style and optional custom overrides"""
        self.style = self.DEFAULT_STYLE.copy()
        if custom_style:
            self._merge_styles(self.style, custom_style)

    def _merge_styles(self, base: Dict, custom: Dict):
        """Recursively merge custom styles into base"""
        for key, value in custom.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_styles(base[key], value)
            else:
                base[key] = value

    def generate_css(self) -> str:
        """Generate CSS from configuration"""
        s = self.style

        css = f"""
        /* Page Setup */
        @page {{
            size: {s['page']['size']};
            margin-top: {s['page']['margin_top']};
            margin-bottom: {s['page']['margin_bottom']};
            margin-left: {s['page']['margin_left']};
            margin-right: {s['page']['margin_right']};
        }}

        /* Body */
        body {{
            font-family: {s['fonts']['body_family']};
            font-size: {s['fonts']['body_size']};
            color: {s['fonts']['body_color']};
            line-height: {s['fonts']['body_line_height']};
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        /* Headings */
        h1 {{
            font-family: {s['fonts']['heading1_family']};
            font-size: {s['fonts']['heading1_size']};
            color: {s['fonts']['heading1_color']};
            font-weight: {s['fonts']['heading1_weight']};
            margin-top: {s['spacing']['heading1_margin_top']};
            margin-bottom: {s['spacing']['heading1_margin_bottom']};
            text-align: center;
        }}

        h2 {{
            font-family: {s['fonts']['heading2_family']};
            font-size: {s['fonts']['heading2_size']};
            color: {s['fonts']['heading2_color']};
            font-weight: {s['fonts']['heading2_weight']};
            margin-top: {s['spacing']['heading2_margin_top']};
            margin-bottom: {s['spacing']['heading2_margin_bottom']};
            text-transform: uppercase;
        }}

        h3 {{
            font-family: {s['fonts']['heading3_family']};
            font-size: {s['fonts']['heading3_size']};
            color: {s['fonts']['heading3_color']};
            font-weight: {s['fonts']['heading3_weight']};
            margin-top: {s['spacing']['heading3_margin_top']};
            margin-bottom: {s['spacing']['heading3_margin_bottom']};
        }}

        /* Paragraphs */
        p {{
            margin: {s['spacing']['paragraph_spacing']} 0;
        }}

        /* Lists */
        ul {{
            margin: {s['spacing']['list_spacing']} 0;
            padding-left: {s['lists']['indent']};
            list-style-type: {s['lists']['bullet_style']};
        }}

        li {{
            margin: {s['spacing']['list_spacing']} 0;
            {f"color: {s['lists']['bullet_color']};" if s['lists']['bullet_color'] else ""}
        }}

        /* Bold */
        strong, b {{
            font-weight: {s['bold']['weight']};
            {f"color: {s['bold']['color']};" if s['bold']['color'] else ""}
        }}

        /* Horizontal rules */
        hr {{
            display: {s['horizontal_rule']['display']};
            border: {s['horizontal_rule']['border']};
            border-top: {s['horizontal_rule']['border_top']};
            margin: {s['horizontal_rule']['margin']};
        }}

        /* First paragraph after heading (summary) */
        h1 + p {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 0.5em;
        }}

        /* Second paragraph (tagline/summary) */
        h1 + p + p {{
            text-align: justify;
            margin-bottom: 1em;
        }}
        """

        return css

    def save_config(self, path: str):
        """Save current configuration to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.style, f, indent=2)

    @classmethod
    def load_config(cls, path: str):
        """Load configuration from JSON file"""
        with open(path, 'r') as f:
            custom_style = json.load(f)
        return cls(custom_style)


class MarkdownToPDF:
    """Convert markdown to PDF with custom styling"""

    def __init__(self, style_config: PDFStyleConfig = None):
        """Initialize converter with optional custom style"""
        self.style_config = style_config or PDFStyleConfig()

    def convert(self, markdown_path: str, output_pdf: str = None) -> str:
        """
        Convert markdown file to PDF

        Args:
            markdown_path: Path to markdown file
            output_pdf: Output PDF path (optional)

        Returns:
            Path to generated PDF
        """
        markdown_path = Path(markdown_path)

        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

        if output_pdf is None:
            output_pdf = markdown_path.with_suffix('.pdf')
        else:
            output_pdf = Path(output_pdf)

        print(f"📄 Converting Markdown to PDF")
        print(f"   Input:  {markdown_path}")
        print(f"   Output: {output_pdf}")

        # Read markdown
        with open(markdown_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert markdown to HTML
        print(f"   ✓ Converting markdown to HTML...")
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'nl2br']  # Support tables, fenced code, etc.
        )

        # Generate CSS
        css = self.style_config.generate_css()

        # Create full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                {css}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Convert to PDF
        print(f"   ✓ Generating PDF...")

        # Try Playwright first (works great on Windows)
        try:
            from playwright.sync_api import sync_playwright

            # Extract margin settings from style config
            margins = self.style_config.style['page']

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(full_html)
                page.pdf(
                    path=str(output_pdf),
                    format='A4',
                    margin={
                        'top': margins['margin_top'],
                        'bottom': margins['margin_bottom'],
                        'left': margins['margin_left'],
                        'right': margins['margin_right'],
                    },
                    print_background=True,  # Ensure backgrounds/colors print
                )
                browser.close()

            print(f"   ✅ PDF created successfully! (Playwright)")
            return str(output_pdf)

        except ImportError:
            print(f"   ℹ️  Playwright not installed, trying WeasyPrint...")
        except Exception as e:
            print(f"   ⚠️  Playwright failed: {e}")
            print(f"   ℹ️  Trying WeasyPrint...")

        # Try WeasyPrint as fallback (works on Linux/Mac)
        try:
            from weasyprint import HTML
            HTML(string=full_html).write_pdf(output_pdf)
            print(f"   ✅ PDF created successfully! (WeasyPrint)")
            return str(output_pdf)

        except (ImportError, OSError) as e:
            # Last resort: save HTML for manual conversion
            html_path = output_pdf.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(full_html)

            print(f"   ⚠️  No PDF library available")
            print(f"   ℹ️  HTML saved to: {html_path}")
            print(f"\n   💡 Install Playwright for automated PDF:")
            print(f"      pip install playwright")
            print(f"      playwright install chromium")
            print(f"\n   Or manually:")
            print(f"      1. Open HTML in browser and print to PDF")
            print(f"      2. Use online HTML to PDF converter")

            return str(html_path)

        return str(output_pdf)


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert Markdown to beautifully styled PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s cv.md

  # Custom output name
  %(prog)s cv.md -o MyCV.pdf

  # Use custom style config
  %(prog)s cv.md --style my_style.json

  # Save default style config for editing
  %(prog)s --save-config default_style.json
        """
    )

    parser.add_argument('markdown', nargs='?', help='Path to markdown file')
    parser.add_argument('-o', '--output', help='Output PDF path')
    parser.add_argument('--style', help='Path to style config JSON')
    parser.add_argument('--save-config', help='Save default style config to file')

    args = parser.parse_args()

    # Save config mode
    if args.save_config:
        config = PDFStyleConfig()
        config.save_config(args.save_config)
        print(f"✅ Default style config saved to: {args.save_config}")
        print(f"   Edit this file to customize styling, then use with --style flag")
        return

    # Convert mode
    if not args.markdown:
        parser.error("markdown file is required (unless using --save-config)")

    # Load style config
    if args.style:
        print(f"📋 Loading custom style: {args.style}")
        style_config = PDFStyleConfig.load_config(args.style)
    else:
        style_config = PDFStyleConfig()

    # Convert
    converter = MarkdownToPDF(style_config)

    try:
        output_path = converter.convert(args.markdown, args.output)
        print()
        print("=" * 80)
        print(f"✅ SUCCESS! Generated: {output_path}")
        print("=" * 80)
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
