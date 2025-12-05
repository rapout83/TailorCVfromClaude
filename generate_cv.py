#!/usr/bin/env python3
"""
Unified CV Generator - Complete pipeline from Markdown to DOCX + PDF

Usage:
    python generate_cv.py <markdown_file> <template_file> [--strict]

Examples:
    # Basic usage
    python generate_cv.py cv.md template.docx

    # Strict validation (fail on warnings)
    python generate_cv.py cv.md template.docx --strict

    # Or import and use programmatically
    from generate_cv import generate_cv_from_markdown
    generate_cv_from_markdown("cv.md", "template.docx")
"""

import sys
import argparse
from pathlib import Path
from cv_generator import CVParser, CVValidator
from docx_populator import DOCXPopulator
from pdf_generator_v2 import docx_to_pdf_via_html


def generate_cv_from_markdown(
    markdown_path: str,
    template_path: str,
    output_dir: str = None,
    output_name: str = None,
    strict_mode: bool = False,
    skip_pdf: bool = False
) -> dict:
    """
    Generate DOCX and PDF from markdown CV

    Args:
        markdown_path: Path to markdown CV file
        template_path: Path to DOCX template
        output_dir: Output directory (defaults to current dir)
        output_name: Base name for output files (defaults to input filename)
        strict_mode: If True, fail on any validation warnings
        skip_pdf: If True, only generate DOCX

    Returns:
        dict with paths to generated files and validation results
    """
    print("=" * 80)
    print("CV GENERATOR - Complete Pipeline")
    print("=" * 80)
    print()

    # Setup paths
    markdown_path = Path(markdown_path)
    template_path = Path(template_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    if output_name is None:
        output_name = markdown_path.stem

    # Output paths
    output_docx = output_dir / f"{output_name}.docx"
    output_pdf = output_dir / f"{output_name}.pdf"

    # Step 1: Load and parse markdown
    print("📄 Step 1: Loading Markdown")
    print(f"   File: {markdown_path}")
    with open(markdown_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    parser = CVParser(md_content)
    cv_data = parser.parse()

    print(f"   ✅ Parsed {len(parser.get_section_list())} sections")
    for section in parser.get_section_list():
        print(f"      - {section}")
    print()

    # Step 2: Validate
    print("✅ Step 2: Validation")
    print(f"   Template: {template_path}")

    validator = CVValidator(str(template_path))
    validation_result = validator.validate(cv_data)

    if validation_result.errors:
        print("\n   ❌ ERRORS:")
        for error in validation_result.errors:
            print(f"      - {error}")

    if validation_result.warnings:
        print("\n   ⚠️  WARNINGS:")
        for warning in validation_result.warnings:
            print(f"      - {warning}")

    if validation_result.missing_in_template:
        print("\n   📝 Will skip (in markdown, not in template):")
        for section in validation_result.missing_in_template:
            print(f"      - {section}")

    if not validation_result.is_valid:
        print("\n   ❌ VALIDATION FAILED")
        raise ValueError("Validation errors found. Fix them before proceeding.")

    if strict_mode and validation_result.warnings:
        print("\n   ❌ STRICT MODE: Failing due to warnings")
        raise ValueError("Validation warnings in strict mode")

    print("\n   ✅ Validation passed")
    print()

    # Step 3: Generate DOCX
    print("📝 Step 3: Generating DOCX")
    print(f"   Output: {output_docx}")

    populator = DOCXPopulator(str(template_path), cv_data)
    doc = populator.populate_all()
    populator.save(str(output_docx))

    result = {
        'docx': str(output_docx),
        'validation': validation_result
    }

    # Step 4: Generate PDF
    if not skip_pdf:
        print()
        print("📄 Step 4: Generating PDF")
        print(f"   Output: {output_pdf}")

        try:
            pdf_path = docx_to_pdf_via_html(str(output_docx), str(output_pdf))
            result['pdf'] = pdf_path
            print(f"   ✅ PDF created")
        except Exception as e:
            print(f"   ⚠️  PDF generation failed: {e}")
            print(f"   ℹ️  DOCX is still available at: {output_docx}")
            result['pdf_error'] = str(e)

    # Summary
    print()
    print("=" * 80)
    print("✅ GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("📁 Generated Files:")
    print(f"   DOCX: {output_docx}")
    if 'pdf' in result:
        print(f"   PDF:  {output_pdf}")
    print()

    if validation_result.warnings:
        print("⚠️  Note: Some sections were skipped due to template mismatches")
        print("   Review warnings above for details")
        print()

    return result


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='Generate CV in DOCX and PDF formats from Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s cv.md template.docx
  %(prog)s cv.md template.docx --output-dir ./output
  %(prog)s cv.md template.docx --output-name "John_Doe_CV" --strict
        """
    )

    parser.add_argument('markdown', help='Path to markdown CV file')
    parser.add_argument('template', help='Path to DOCX template file')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: current dir)')
    parser.add_argument('--output-name', '-n', help='Base name for output files (default: markdown filename)')
    parser.add_argument('--strict', action='store_true', help='Fail on validation warnings')
    parser.add_argument('--skip-pdf', action='store_true', help='Only generate DOCX, skip PDF')

    args = parser.parse_args()

    try:
        result = generate_cv_from_markdown(
            markdown_path=args.markdown,
            template_path=args.template,
            output_dir=args.output_dir,
            output_name=args.output_name,
            strict_mode=args.strict,
            skip_pdf=args.skip_pdf
        )

        sys.exit(0)

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
