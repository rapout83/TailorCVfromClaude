#!/usr/bin/env python3
"""
PDF Generator - Convert DOCX to PDF
"""

import subprocess
import os
from pathlib import Path


class PDFGenerator:
    """Generate PDF from DOCX file"""

    @staticmethod
    def docx_to_pdf_libreoffice(docx_path: str, output_dir: str = None) -> str:
        """
        Convert DOCX to PDF using LibreOffice headless mode

        Args:
            docx_path: Path to DOCX file
            output_dir: Output directory (defaults to same as DOCX)

        Returns:
            Path to generated PDF file
        """
        docx_path = Path(docx_path).absolute()

        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")

        if output_dir is None:
            output_dir = docx_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        output_dir = output_dir.absolute()

        print(f"📄 Converting DOCX to PDF...")
        print(f"   Input:  {docx_path}")
        print(f"   Output: {output_dir}")

        try:
            # Try LibreOffice (most common on Linux)
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_dir),
                str(docx_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            # Calculate PDF filename
            pdf_filename = docx_path.stem + '.pdf'
            pdf_path = output_dir / pdf_filename

            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF was not created: {pdf_path}")

            print(f"✅ PDF created: {pdf_path}")
            return str(pdf_path)

        except FileNotFoundError as e:
            if 'libreoffice' in str(e).lower():
                print("❌ LibreOffice not found. Trying alternative methods...")
                return PDFGenerator._try_alternative_methods(docx_path, output_dir)
            raise

    @staticmethod
    def _try_alternative_methods(docx_path: Path, output_dir: Path) -> str:
        """Try alternative PDF conversion methods"""

        # Try unoconv
        try:
            cmd = ['unoconv', '-f', 'pdf', '-o', str(output_dir), str(docx_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                pdf_path = output_dir / (docx_path.stem + '.pdf')
                if pdf_path.exists():
                    print(f"✅ PDF created with unoconv: {pdf_path}")
                    return str(pdf_path)
        except FileNotFoundError:
            pass

        # Try docx2pdf (requires Windows or LibreOffice)
        try:
            from docx2pdf import convert
            pdf_path = output_dir / (docx_path.stem + '.pdf')
            convert(str(docx_path), str(pdf_path))

            if pdf_path.exists():
                print(f"✅ PDF created with docx2pdf: {pdf_path}")
                return str(pdf_path)
        except ImportError:
            pass
        except Exception as e:
            print(f"   docx2pdf failed: {e}")

        raise RuntimeError(
            "Could not convert DOCX to PDF. Please install LibreOffice:\n"
            "  Ubuntu/Debian: sudo apt-get install libreoffice\n"
            "  CentOS/RHEL: sudo yum install libreoffice\n"
            "  macOS: brew install libreoffice"
        )

    @staticmethod
    def convert(docx_path: str, output_dir: str = None) -> str:
        """
        Convert DOCX to PDF (convenience method)

        Args:
            docx_path: Path to DOCX file
            output_dir: Output directory (optional)

        Returns:
            Path to generated PDF
        """
        return PDFGenerator.docx_to_pdf_libreoffice(docx_path, output_dir)


def main():
    """Test PDF generation"""
    import sys

    print("=" * 80)
    print("PDF GENERATOR TEST")
    print("=" * 80)
    print()

    # Check if output_cv.docx exists
    docx_file = "output_cv.docx"

    if not os.path.exists(docx_file):
        print(f"❌ Error: {docx_file} not found.")
        print("   Run docx_populator.py first to create the DOCX file.")
        sys.exit(1)

    try:
        pdf_path = PDFGenerator.convert(docx_file)

        print()
        print("=" * 80)
        print(f"✅ SUCCESS! PDF generated: {pdf_path}")

        # Show file size
        pdf_size = os.path.getsize(pdf_path)
        print(f"   File size: {pdf_size / 1024:.1f} KB")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
