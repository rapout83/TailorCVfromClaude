#!/usr/bin/env python3
"""
DOCX Populator - Replace template content with markdown CV data
"""

import re
from typing import Dict, List, Optional, Tuple
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from copy import deepcopy
import os


class DOCXPopulator:
    """Populate DOCX template with markdown CV content"""

    def __init__(self, template_path: str, cv_data: Dict[str, any]):
        self.template_path = template_path
        self.cv_data = cv_data
        self.doc = Document(template_path)

    def _find_paragraph_index(self, search_text: str, case_sensitive=False) -> Optional[int]:
        """Find paragraph index containing search text"""
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text if case_sensitive else para.text.upper()
            search = search_text if case_sensitive else search_text.upper()
            if search in text:
                return i
        return None

    def _find_section_range(self, section_header: str) -> Optional[Tuple[int, int]]:
        """Find start and end paragraph indices for a section"""
        start_idx = self._find_paragraph_index(section_header)
        if start_idx is None:
            return None

        # Find next section header (or end of document)
        end_idx = len(self.doc.paragraphs)
        section_headers = [
            'CORE COMPETENCIES', 'PROFESSIONAL EXPERIENCE',
            'EDUCATION', 'CERTIFICATION', 'LANGUAGES'
        ]

        for i in range(start_idx + 1, len(self.doc.paragraphs)):
            para_text = self.doc.paragraphs[i].text.upper()
            # Check if this is a new section header
            if any(header in para_text for header in section_headers):
                end_idx = i
                break

        return (start_idx, end_idx)

    def _clear_paragraphs(self, start_idx: int, end_idx: int, keep_first=True):
        """Clear paragraphs between indices"""
        # Delete from end to start to avoid index shifting
        start = start_idx + 1 if keep_first else start_idx
        for i in range(end_idx - 1, start - 1, -1):
            if i < len(self.doc.paragraphs):
                p = self.doc.paragraphs[i]
                # Remove the paragraph element
                p._element.getparent().remove(p._element)

    def _add_paragraph_after(self, index: int, text: str, style=None, bold=False):
        """Add a new paragraph after the given index"""
        if index >= len(self.doc.paragraphs):
            para = self.doc.add_paragraph(text, style=style)
        else:
            # Insert after specific paragraph
            p = self.doc.paragraphs[index]._element
            new_p = self.doc.add_paragraph(text, style=style)._element
            p.addnext(new_p)
            # Refresh doc paragraphs
            para = self.doc.paragraphs[index + 1]

        if bold and para.runs:
            para.runs[0].bold = True

        return para

    def _parse_markdown_list(self, content: str) -> List[str]:
        """Parse markdown bullet points"""
        bullets = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                bullets.append(line[2:].strip())
        return bullets

    def populate_achievements(self):
        """Populate signature achievements (bullets after summary)"""
        print("  📝 Populating Signature Achievements...")

        achievements_content = self.cv_data.get('SIGNATURE ACHIEVEMENTS', '')
        if not achievements_content:
            print("     ⚠️  No achievements found in markdown")
            return

        # Find the summary paragraph (line 3 in our analysis)
        # Then replace the achievement bullets (lines 4-7)
        bullets = self._parse_markdown_list(achievements_content)

        # Find where achievements should go (after summary, before CORE COMPETENCIES)
        summary_idx = None
        for i, para in enumerate(self.doc.paragraphs):
            if 'Proven track record' in para.text or i == 3:  # Line 3 from analysis
                summary_idx = i
                break

        if summary_idx is None:
            print("     ⚠️  Could not find summary paragraph")
            return

        # Find end of achievements section (before CORE COMPETENCIES)
        core_comp_idx = self._find_paragraph_index('CORE COMPETENCIES')
        if core_comp_idx is None:
            print("     ⚠️  Could not find CORE COMPETENCIES section")
            return

        # Clear existing achievement bullets
        self._clear_paragraphs(summary_idx + 1, core_comp_idx, keep_first=False)

        # Add new achievement bullets
        current_idx = summary_idx
        for bullet in bullets:
            # Clean markdown formatting
            bullet_text = bullet.replace('**', '')
            # Add as List Paragraph style (matching template)
            self._add_paragraph_after(current_idx, bullet_text, style='List Paragraph')
            current_idx += 1

        print(f"     ✅ Added {len(bullets)} achievements")

    def populate_core_competencies(self):
        """Populate core competencies section"""
        print("  📝 Populating Core Competencies...")

        competencies_content = self.cv_data.get('CORE COMPETENCIES', '')
        if not competencies_content:
            print("     ⚠️  No competencies found in markdown")
            return

        section_range = self._find_section_range('CORE COMPETENCIES')
        if not section_range:
            print("     ⚠️  Could not find CORE COMPETENCIES section in template")
            return

        start_idx, end_idx = section_range

        # Parse competency subsections from markdown
        lines = competencies_content.strip().split('\n')
        subsections = []
        for line in lines:
            if line.startswith('**') and ':' in line:
                # This is a subsection like "**Platform Leadership:** ..."
                subsections.append(line.strip())

        # Clear existing content
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        # Add new competencies
        current_idx = start_idx
        for subsection in subsections:
            # Clean and format
            text = subsection.replace('**', '')
            self._add_paragraph_after(current_idx, text, style='Normal')
            current_idx += 1

        print(f"     ✅ Added {len(subsections)} competency areas")

    def populate_experience(self):
        """Populate professional experience section"""
        print("  📝 Populating Professional Experience...")

        experience_content = self.cv_data.get('PROFESSIONAL EXPERIENCE', '')
        if not experience_content:
            print("     ⚠️  No experience found in markdown")
            return

        section_range = self._find_section_range('PROFESSIONAL EXPERIENCE')
        if not section_range:
            print("     ⚠️  Could not find PROFESSIONAL EXPERIENCE section in template")
            return

        start_idx, end_idx = section_range

        # Clear existing content
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        # Parse experience entries from markdown
        # Split by ### (job entries)
        jobs = re.split(r'\n### ', experience_content)

        current_idx = start_idx
        for job in jobs:
            if not job.strip():
                continue

            lines = job.strip().split('\n')
            if not lines:
                continue

            # First line is the job title/company/dates
            job_header = lines[0].replace('**', '').strip()
            self._add_paragraph_after(current_idx, job_header, style='Normal', bold=True)
            current_idx += 1

            # Parse rest of content
            for line in lines[1:]:
                line = line.strip()
                if not line or line.startswith('---'):
                    continue

                # Check if it's a subheading (all caps)
                if line.isupper() and len(line) < 100:
                    self._add_paragraph_after(current_idx, line, style='Normal', bold=True)
                    current_idx += 1
                # Check if it's a bullet point
                elif line.startswith('- '):
                    bullet_text = line[2:].replace('**', '')
                    self._add_paragraph_after(current_idx, bullet_text, style='List Paragraph')
                    current_idx += 1
                # Regular paragraph
                else:
                    self._add_paragraph_after(current_idx, line, style='Normal')
                    current_idx += 1

        print(f"     ✅ Added experience entries")

    def populate_education(self):
        """Populate education section"""
        print("  📝 Populating Education...")

        education_content = self.cv_data.get('EDUCATION', '')
        if not education_content:
            print("     ⚠️  No education found in markdown")
            return

        section_range = self._find_section_range('EDUCATION')
        if not section_range:
            print("     ⚠️  Could not find EDUCATION section in template")
            return

        start_idx, end_idx = section_range

        # Clear existing content
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        # Add education content
        current_idx = start_idx
        lines = education_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('---'):
                # Remove markdown formatting
                text = line.replace('**', '').replace('*', '')
                self._add_paragraph_after(current_idx, text, style='Normal')
                current_idx += 1

        print(f"     ✅ Added education")

    def populate_certifications(self):
        """Populate certifications section"""
        print("  📝 Populating Certifications...")

        certs_content = self.cv_data.get('CERTIFICATIONS', '')
        if not certs_content:
            print("     ⚠️  No certifications found in markdown")
            return

        # Template uses "CERTIFICATION" (singular)
        section_range = self._find_section_range('CERTIFICATION')
        if not section_range:
            print("     ⚠️  Could not find CERTIFICATION section in template")
            return

        start_idx, end_idx = section_range

        # Clear existing content
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        # Add certifications
        current_idx = start_idx
        lines = certs_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('---'):
                self._add_paragraph_after(current_idx, line, style='Normal')
                current_idx += 1

        print(f"     ✅ Added certifications")

    def populate_all(self) -> Document:
        """Populate all sections"""
        print("\n🔄 Populating DOCX template...")

        self.populate_achievements()
        self.populate_core_competencies()
        self.populate_experience()
        self.populate_education()
        self.populate_certifications()

        print("✅ Population complete!")

        return self.doc

    def save(self, output_path: str):
        """Save populated document"""
        self.doc.save(output_path)
        print(f"\n💾 Saved to: {output_path}")


def main():
    """Test the populator"""
    from cv_generator import CVParser

    print("=" * 80)
    print("DOCX POPULATOR TEST")
    print("=" * 80)

    # Load and parse markdown
    md_file = "Henry_Jung_CV_Imperial_Brands_Head_Enterprise_Data_Platforms.md"
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    parser = CVParser(md_content)
    cv_data = parser.parse()

    # Populate template
    template_file = "Henry Jung_CV_Imperial Brands PLC.docx"
    output_file = "output_cv.docx"

    populator = DOCXPopulator(template_file, cv_data)
    populator.populate_all()
    populator.save(output_file)

    print("\n" + "=" * 80)
    print(f"✅ SUCCESS! Check the output file: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
