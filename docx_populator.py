#!/usr/bin/env python3
"""
DOCX Populator - Replace template content with markdown CV data (FIXED VERSION)
"""

import re
from typing import Dict, List, Optional, Tuple
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from copy import deepcopy


class DOCXPopulator:
    """Populate DOCX template with markdown CV content"""

    def __init__(self, template_path: str, cv_data: Dict[str, any]):
        self.template_path = template_path
        self.cv_data = cv_data
        self.doc = Document(template_path)
        # Store reference paragraphs for styling
        self._reference_styles = self._extract_reference_styles()

    def _extract_reference_styles(self) -> Dict:
        """Extract reference paragraph styles from template"""
        styles = {}
        for para in self.doc.paragraphs:
            if para.style.name not in styles:
                styles[para.style.name] = para
        return styles

    def _clean_markdown(self, text: str) -> str:
        """Remove all markdown syntax from text"""
        if not text:
            return text

        # Remove markdown syntax (order matters!)
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # Bold italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)          # Italic
        text = re.sub(r'___(.+?)___', r'\1', text)        # Bold italic
        text = re.sub(r'__(.+?)__', r'\1', text)          # Bold
        text = re.sub(r'_(.+?)_', r'\1', text)            # Italic
        text = re.sub(r'###\s*', '', text)                # H3 (allow no space)
        text = re.sub(r'##\s*', '', text)                 # H2 (allow no space)
        text = re.sub(r'#\s*', '', text)                  # H1 (allow no space)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)   # Links
        text = re.sub(r'`(.+?)`', r'\1', text)            # Code

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _extract_bold_text(self, text: str) -> List[Tuple[str, bool]]:
        """Extract text with bold formatting info, preserving spaces"""
        if not text:
            return [(text, False)]

        # Find **bold** patterns
        parts = []
        last_end = 0

        for match in re.finditer(r'\*\*([^*]+?)\*\*', text):
            # Add text before bold
            if match.start() > last_end:
                before_text = text[last_end:match.start()]
                # Clean markdown but preserve spaces
                before_text = re.sub(r'###\s*', '', before_text)
                if before_text:
                    parts.append((before_text, False))
            # Add bold text
            parts.append((match.group(1), True))
            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            # Clean any remaining markdown
            remaining = re.sub(r'###\s*', '', remaining)
            if remaining:
                parts.append((remaining, False))

        # If no bold patterns found, return cleaned text
        if not parts:
            cleaned = self._clean_markdown(text)
            return [(cleaned, False)] if cleaned else []

        return parts

    def _add_bullet_formatting(self, para):
        """Add bullet point formatting to a paragraph"""
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls

        # Add numbering/bullet formatting
        pPr = para._element.get_or_add_pPr()
        numPr = parse_xml(r'<w:numPr %s><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>' % nsdecls('w'))
        pPr.insert(0, numPr)

    def _add_paragraph_with_formatting(self, index: int, text: str, style_name='Normal', is_bullet=False):
        """Add paragraph with proper formatting, Calibri 10, and bullets"""
        # Get text parts with bold info
        parts = self._extract_bold_text(text)

        # Create paragraph
        if index >= len(self.doc.paragraphs):
            para = self.doc.add_paragraph(style=style_name)
        else:
            p = self.doc.paragraphs[index]._element
            new_p = self.doc.add_paragraph(style=style_name)._element
            p.addnext(new_p)
            para = self.doc.paragraphs[index + 1]

        # Add bullet formatting if needed
        if is_bullet:
            try:
                self._add_bullet_formatting(para)
            except Exception:
                # If bullet formatting fails, at least keep the text
                pass

        # Add text with formatting
        for text_part, is_bold in parts:
            if text_part:
                run = para.add_run(text_part)
                run.bold = is_bold
                # Set font to Calibri 10
                run.font.name = 'Calibri'
                run.font.size = Pt(10)

        return para

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

        end_idx = len(self.doc.paragraphs)
        section_headers = [
            'CORE COMPETENCIES', 'PROFESSIONAL EXPERIENCE',
            'EDUCATION', 'CERTIFICATION', 'LANGUAGES'
        ]

        for i in range(start_idx + 1, len(self.doc.paragraphs)):
            para_text = self.doc.paragraphs[i].text.upper()
            if any(header in para_text for header in section_headers):
                end_idx = i
                break

        return (start_idx, end_idx)

    def _clear_paragraphs(self, start_idx: int, end_idx: int, keep_first=True):
        """Clear paragraphs between indices"""
        start = start_idx + 1 if keep_first else start_idx
        for i in range(end_idx - 1, start - 1, -1):
            if i < len(self.doc.paragraphs):
                p = self.doc.paragraphs[i]
                p._element.getparent().remove(p._element)

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

        bullets = self._parse_markdown_list(achievements_content)

        # Find summary and core competencies indices
        summary_idx = None
        for i, para in enumerate(self.doc.paragraphs):
            if 'Proven track record' in para.text or i == 3:
                summary_idx = i
                break

        if summary_idx is None:
            print("     ⚠️  Could not find summary paragraph")
            return

        core_comp_idx = self._find_paragraph_index('CORE COMPETENCIES')
        if core_comp_idx is None:
            print("     ⚠️  Could not find CORE COMPETENCIES section")
            return

        # Clear existing bullets
        self._clear_paragraphs(summary_idx + 1, core_comp_idx, keep_first=False)

        # Add new achievement bullets with formatting
        current_idx = summary_idx
        for bullet in bullets:
            self._add_paragraph_with_formatting(current_idx, bullet, style_name='List Paragraph', is_bullet=True)
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

        # Parse competency subsections
        lines = competencies_content.strip().split('\n')
        subsections = []
        for line in lines:
            if line.strip() and not line.startswith('---'):
                subsections.append(line.strip())

        # Clear existing content
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        # Add new competencies
        current_idx = start_idx
        for subsection in subsections:
            self._add_paragraph_with_formatting(current_idx, subsection, style_name='Normal')
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
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        # Parse experience entries
        jobs = re.split(r'\n### ', experience_content)

        current_idx = start_idx
        for job in jobs:
            if not job.strip():
                continue

            lines = job.strip().split('\n')
            if not lines:
                continue

            # Job header (title/company/dates)
            job_header = lines[0].strip()
            self._add_paragraph_with_formatting(current_idx, job_header, style_name='Normal')
            current_idx += 1

            # Process rest of content
            for line in lines[1:]:
                line = line.strip()
                if not line or line.startswith('---'):
                    continue

                # Subheading (all caps)
                if line.isupper() and len(line) < 100:
                    self._add_paragraph_with_formatting(current_idx, line, style_name='Normal')
                    current_idx += 1
                # Bullet point
                elif line.startswith('- '):
                    bullet_text = line[2:].strip()
                    self._add_paragraph_with_formatting(current_idx, bullet_text, style_name='List Paragraph', is_bullet=True)
                    current_idx += 1
                # Regular paragraph
                else:
                    self._add_paragraph_with_formatting(current_idx, line, style_name='Normal')
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
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        current_idx = start_idx
        lines = education_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('---'):
                self._add_paragraph_with_formatting(current_idx, line, style_name='Normal')
                current_idx += 1

        print(f"     ✅ Added education")

    def populate_certifications(self):
        """Populate certifications section"""
        print("  📝 Populating Certifications...")

        certs_content = self.cv_data.get('CERTIFICATIONS', '')
        if not certs_content:
            print("     ⚠️  No certifications found in markdown")
            return

        section_range = self._find_section_range('CERTIFICATION')
        if not section_range:
            print("     ⚠️  Could not find CERTIFICATION section in template")
            return

        start_idx, end_idx = section_range
        self._clear_paragraphs(start_idx + 1, end_idx, keep_first=False)

        current_idx = start_idx
        lines = certs_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('---'):
                cleaned_line = self._clean_markdown(line)
                self._add_paragraph_with_formatting(current_idx, cleaned_line, style_name='Normal')
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

    md_file = "Henry_Jung_CV_Imperial_Brands_Head_Enterprise_Data_Platforms.md"
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    parser = CVParser(md_content)
    cv_data = parser.parse()

    template_file = "Henry Jung_CV_Imperial Brands PLC.docx"
    output_file = "output_cv_fixed.docx"

    populator = DOCXPopulator(template_file, cv_data)
    populator.populate_all()
    populator.save(output_file)

    print("\n" + "=" * 80)
    print(f"✅ SUCCESS! Check the output file: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
