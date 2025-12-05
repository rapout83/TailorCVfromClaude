#!/usr/bin/env python3
"""
CV Generator - Convert Markdown CV to DOCX template with validation
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from docx import Document
from pathlib import Path
import json


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_in_template: List[str]
    missing_in_markdown: List[str]


class CVParser:
    """Parse markdown CV into structured sections"""

    def __init__(self, markdown_content: str):
        self.content = markdown_content
        self.sections = {}

    def parse(self) -> Dict[str, any]:
        """Parse markdown into structured data"""
        lines = self.content.split('\n')

        # Extract header (name and tagline)
        self.sections['name'] = lines[0].replace('#', '').strip()
        self.sections['tagline'] = lines[2].replace('**', '').strip() if len(lines) > 2 else ""

        # Extract summary (text before first ##)
        summary_lines = []
        for i, line in enumerate(lines[4:], start=4):
            if line.startswith('##'):
                break
            if line.strip() and not line.startswith('---'):
                summary_lines.append(line.strip())
        self.sections['summary'] = ' '.join(summary_lines)

        # Extract sections by headers
        current_section = None
        current_content = []

        for line in lines:
            # Check for main section headers (##)
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    self.sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = line.replace('##', '').strip()
                current_content = []

            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            self.sections[current_section] = '\n'.join(current_content).strip()

        return self.sections

    def get_section_list(self) -> List[str]:
        """Get list of section names (excluding name, tagline, summary)"""
        return [
            key for key in self.sections.keys()
            if key not in ['name', 'tagline', 'summary']
        ]


class TemplateSchema:
    """Define expected sections in DOCX template"""

    # Define what sections the template expects
    TEMPLATE_SECTIONS = {
        'SIGNATURE_ACHIEVEMENTS': {
            'required': False,
            'aliases': ['SIGNATURE ACHIEVEMENTS', 'KEY ACHIEVEMENTS', 'ACHIEVEMENTS']
        },
        'CORE_COMPETENCIES': {
            'required': True,
            'aliases': ['CORE COMPETENCIES', 'CORE COMPETENCIES & TECHNICAL EXPERTISE']
        },
        'PROFESSIONAL_EXPERIENCE': {
            'required': True,
            'aliases': ['PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'WORK EXPERIENCE']
        },
        'EDUCATION': {
            'required': True,
            'aliases': ['EDUCATION']
        },
        'CERTIFICATIONS': {
            'required': False,
            'aliases': ['CERTIFICATIONS', 'CERTIFICATION']
        },
        'LANGUAGES': {
            'required': False,
            'aliases': ['LANGUAGES', 'LANGUAGE']
        }
    }

    @classmethod
    def normalize_section_name(cls, section_name: str) -> Optional[str]:
        """Normalize section name to standard key"""
        section_upper = section_name.upper().strip()

        for key, config in cls.TEMPLATE_SECTIONS.items():
            if section_upper in [alias.upper() for alias in config['aliases']]:
                return key

        return None


class CVValidator:
    """Validate markdown CV against DOCX template requirements"""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self.template_sections = self._extract_template_sections()

    def _extract_template_sections(self) -> List[str]:
        """Extract section headers from DOCX template"""
        doc = Document(self.template_path)
        sections = []

        # Look for section headers (uppercase text, heading styles, or bold paragraphs)
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # Check if it looks like a section header
                is_header = (
                    text.isupper() or
                    'Heading' in para.style.name or
                    (para.runs and para.runs[0].bold and len(text) < 60)
                )

                # Known section headers
                known_sections = [
                    'SIGNATURE ACHIEVEMENTS', 'CORE COMPETENCIES',
                    'PROFESSIONAL EXPERIENCE', 'EDUCATION',
                    'CERTIFICATION', 'CERTIFICATIONS', 'LANGUAGES'
                ]

                if any(section in text.upper() for section in known_sections):
                    sections.append(text.upper())

        return sections

    def validate(self, cv_sections: Dict[str, any]) -> ValidationResult:
        """Validate CV sections against template"""
        errors = []
        warnings = []
        missing_in_template = []
        missing_in_markdown = []

        # Get markdown section list
        md_sections = [
            key for key in cv_sections.keys()
            if key not in ['name', 'tagline', 'summary']
        ]

        # Normalize section names
        md_sections_normalized = set()
        for section in md_sections:
            normalized = TemplateSchema.normalize_section_name(section)
            if normalized:
                md_sections_normalized.add(normalized)
            else:
                warnings.append(f"Unknown section in markdown: '{section}'")

        # Check for sections in markdown but not in template
        template_sections_normalized = set()
        for section in self.template_sections:
            normalized = TemplateSchema.normalize_section_name(section)
            if normalized:
                template_sections_normalized.add(normalized)

        # Find mismatches
        in_md_not_in_template = md_sections_normalized - template_sections_normalized
        in_template_not_in_md = template_sections_normalized - md_sections_normalized

        # Check missing required sections in markdown
        for key, config in TemplateSchema.TEMPLATE_SECTIONS.items():
            if config['required'] and key not in md_sections_normalized:
                errors.append(f"Required section missing in markdown: {config['aliases'][0]}")

        # Warn about sections in markdown not in template
        for section in in_md_not_in_template:
            section_name = TemplateSchema.TEMPLATE_SECTIONS[section]['aliases'][0]
            missing_in_template.append(section_name)
            warnings.append(
                f"Section '{section_name}' found in markdown but NOT in template. "
                f"This section will be SKIPPED."
            )

        # Warn about sections in template not in markdown
        for section in in_template_not_in_md:
            section_name = TemplateSchema.TEMPLATE_SECTIONS[section]['aliases'][0]
            missing_in_markdown.append(section_name)

            if TemplateSchema.TEMPLATE_SECTIONS[section]['required']:
                errors.append(f"Required section '{section_name}' missing in markdown")
            else:
                warnings.append(
                    f"Optional section '{section_name}' in template but not in markdown. "
                    f"Template section will remain empty."
                )

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_in_template=missing_in_template,
            missing_in_markdown=missing_in_markdown
        )


def main():
    """Main execution"""
    print("=" * 80)
    print("CV GENERATOR - Markdown to DOCX Converter")
    print("=" * 80)
    print()

    # Paths
    md_file = "Henry_Jung_CV_Imperial_Brands_Head_Enterprise_Data_Platforms.md"
    template_file = "Henry Jung_CV_Imperial Brands PLC.docx"

    # Load markdown
    print(f"📄 Loading markdown: {md_file}")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse markdown
    print(f"🔍 Parsing markdown structure...")
    parser = CVParser(md_content)
    cv_data = parser.parse()

    print(f"   Found {len(parser.get_section_list())} sections:")
    for section in parser.get_section_list():
        print(f"   - {section}")
    print()

    # Validate against template
    print(f"✅ Validating against template: {template_file}")
    validator = CVValidator(template_file)
    result = validator.validate(cv_data)

    print()
    print("-" * 80)
    print("VALIDATION RESULTS")
    print("-" * 80)

    if result.errors:
        print("\n❌ ERRORS:")
        for error in result.errors:
            print(f"   - {error}")

    if result.warnings:
        print("\n⚠️  WARNINGS:")
        for warning in result.warnings:
            print(f"   - {warning}")

    if result.missing_in_template:
        print("\n📝 Sections in MARKDOWN but NOT in TEMPLATE (will be skipped):")
        for section in result.missing_in_template:
            print(f"   - {section}")

    if result.missing_in_markdown:
        print("\n📝 Sections in TEMPLATE but NOT in MARKDOWN (will be empty):")
        for section in result.missing_in_markdown:
            print(f"   - {section}")

    print()
    print("-" * 80)

    if result.is_valid:
        print("✅ VALIDATION PASSED - Ready to proceed with conversion")
        print("\nNext steps:")
        print("  1. Review warnings above")
        print("  2. Decide whether to:")
        print("     a) Update markdown to match template (add missing sections)")
        print("     b) Update template to match markdown (add missing sections)")
        print("     c) Proceed with conversion (skip/ignore mismatched sections)")
    else:
        print("❌ VALIDATION FAILED - Cannot proceed")
        print("\nPlease fix the errors above before proceeding.")

    print("=" * 80)


if __name__ == "__main__":
    main()
