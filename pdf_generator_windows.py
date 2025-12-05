#!/usr/bin/env python3
"""
PDF Generator for Windows - Uses docx2pdf (requires MS Word)
"""

from pathlib import Path
import subprocess
import sys


def docx_to_pdf_windows(docx_path: str, output_path: str = None) -> str:
    """
    Convert DOCX to PDF on Windows using docx2pdf (requires MS Word)

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

    print(f"📄 Converting DOCX to PDF (Windows)...")
    print(f"   Input:  {docx_path}")
    print(f"   Output: {output_path}")

    try:
        # Try docx2pdf (requires MS Word installed)
        from docx2pdf import convert
        convert(str(docx_path), str(output_path))

        if output_path.exists():
            print(f"✅ PDF created: {output_path}")
            return str(output_path)

    except ImportError:
        print("\n⚠️  docx2pdf not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "docx2pdf"])
        print("✅ Installed! Please run the command again.")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNOTE: docx2pdf requires Microsoft Word to be installed.")
        print("If you don't have Word, use --skip-pdf flag and convert manually.")
        raise


def main():
    """Test PDF generation"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_generator_windows.py <docx_file>")
        sys.exit(1)

    docx_file = sys.argv[1]

    try:
        pdf_path = docx_to_pdf_windows(docx_file)
        print(f"\n✅ SUCCESS! PDF: {pdf_path}")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
