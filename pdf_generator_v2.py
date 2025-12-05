#!/usr/bin/env python3
"""
PDF Generator V2 - Alternative approach using mammoth + weasyprint
"""

import mammoth
from weasyprint import HTML, CSS
from pathlib import Path


def docx_to_pdf_via_html(docx_path: str, output_path: str = None) -> str:
    """
    Convert DOCX to PDF via HTML intermediate

    Args:
        docx_path: Path to DOCX file
        output_path: Output PDF path (optional)

    Returns:
        Path to generated PDF
    """
    docx_path = Path(docx_path)

    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX not found: {docx_path}")

    if output_path is None:
        output_path = docx_path.with_suffix('.pdf')
    else:
        output_path = Path(output_path)

    print(f"📄 Converting DOCX to PDF (via HTML)...")
    print(f"   Input:  {docx_path}")

    # Step 1: Convert DOCX to HTML
    print("   Step 1: DOCX → HTML")
    with open(docx_path, 'rb') as docx_file:
        result = mammoth.convert_to_html(docx_file)
        html_content = result.value

    # Step 2: Add CSS styling for better PDF output
    css_style = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
        }
        h1 {
            font-size: 18pt;
            margin-bottom: 0.5em;
        }
        h2 {
            font-size: 14pt;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        h3 {
            font-size: 12pt;
            margin-top: 0.8em;
            margin-bottom: 0.4em;
        }
        p {
            margin: 0.3em 0;
        }
        ul {
            margin: 0.5em 0;
            padding-left: 2em;
        }
        li {
            margin: 0.2em 0;
        }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>{css_style}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Step 3: Convert HTML to PDF
    print("   Step 2: HTML → PDF")
    HTML(string=full_html).write_pdf(output_path)

    print(f"✅ PDF created: {output_path}")
    return str(output_path)


def main():
    """Test PDF generation"""
    print("=" * 80)
    print("PDF GENERATOR V2 TEST")
    print("=" * 80)
    print()

    docx_file = "output_cv.docx"

    try:
        pdf_path = docx_to_pdf_via_html(docx_file)

        print()
        print("=" * 80)
        print(f"✅ SUCCESS! PDF: {pdf_path}")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)


if __name__ == "__main__":
    main()
