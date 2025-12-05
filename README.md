# CV Generator - Markdown to DOCX/PDF

Automated CV generation pipeline that converts markdown CVs to professionally formatted DOCX and PDF files using your custom template.

## Features

✅ **Markdown to DOCX Conversion** - Populate your template with CV data from markdown
✅ **Automatic PDF Generation** - Generate PDF alongside DOCX
✅ **Smart Validation** - Detect and handle section mismatches
✅ **Template Preservation** - Maintains your DOCX formatting and styling
✅ **API Webhook** - Receive markdown via POST request for automated processing

## Quick Start

### 1. Command Line Usage

```bash
# Basic usage
python generate_cv.py cv.md template.docx

# Specify output location and name
python generate_cv.py cv.md template.docx --output-dir ./output --output-name "John_Doe_CV"

# Strict validation (fail on warnings)
python generate_cv.py cv.md template.docx --strict

# DOCX only (skip PDF)
python generate_cv.py cv.md template.docx --skip-pdf
```

### 2. Python API Usage

```python
from generate_cv import generate_cv_from_markdown

result = generate_cv_from_markdown(
    markdown_path="cv.md",
    template_path="template.docx",
    output_name="John_Doe_CV"
)

print(f"DOCX: {result['docx']}")
print(f"PDF: {result['pdf']}")
```

### 3. Webhook API (for automation)

```bash
# Start the webhook server
python webhook_api.py

# Send markdown CV via POST request
curl -X POST http://localhost:5000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# JOHN DOE\n\n**Software Engineer**...",
    "template_name": "template.docx"
  }'
```

## How It Works

```
┌─────────────┐
│  Markdown   │
│     CV      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Validate  │ ◄── Check sections match template
│   Sections  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Populate   │
│    DOCX     │ ◄── Your template with formatting
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Generate   │
│     PDF     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Output    │
│ DOCX + PDF  │
└─────────────┘
```

## Validation & Section Matching

The generator validates your markdown against the template and provides:

**✅ Passes if:**
- All required sections are present
- Sections can be mapped to template

**⚠️ Warns if:**
- Markdown has sections not in template (will be skipped)
- Template has sections not in markdown (will be empty)

**❌ Fails if:**
- Required sections are missing from markdown

### Example Validation Output

```
⚠️  WARNINGS:
   - Section 'LANGUAGES' found in markdown but NOT in template. This section will be SKIPPED.

📝 Will skip (in markdown, not in template):
   - LANGUAGES
```

## Project Structure

```
├── generate_cv.py           # Main CLI and unified pipeline
├── cv_generator.py          # Markdown parser and validator
├── docx_populator.py        # DOCX template populator
├── pdf_generator_v2.py      # PDF generation (mammoth + weasyprint)
├── webhook_api.py           # Flask API for automation
├── analyze_docx.py          # DOCX structure analyzer (dev tool)
└── README.md                # This file
```

## Requirements

```bash
pip install python-docx mammoth weasyprint
```

## Markdown Format

Your markdown CV should follow this structure:

```markdown
# FULL NAME

**Professional Title/Tagline**

Summary paragraph here...

---

## SIGNATURE ACHIEVEMENTS

- Achievement 1
- Achievement 2
- Achievement 3

---

## CORE COMPETENCIES

**Category 1:** Skill, Skill, Skill
**Category 2:** Skill, Skill, Skill

---

## PROFESSIONAL EXPERIENCE

### Job Title | Company, Location | YYYY–Present

**PROJECT TITLE OR SUMMARY**

Description paragraph...

- Bullet point achievement 1
- Bullet point achievement 2

---

## EDUCATION

**Degree Name** | University, Location
Additional details...

---

## CERTIFICATIONS

Certification Name | Issuing Organization
Another Certification | Issuer

---

## LANGUAGES

English (Fluent) | Spanish (Native)
```

## Automation Workflow

### Seamless Integration with Claude

1. **In Claude Chat** (where you create CVs):
   ```
   User: "Send this CV to my generator"
   Claude: Makes POST request to your webhook
   ```

2. **Webhook receives markdown** and processes automatically

3. **Files generated** and saved to configured location

4. **Optional**: Auto-upload to Notion, email, or cloud storage

### Setup Webhook for Automation

```bash
# 1. Start webhook server
python webhook_api.py

# 2. Expose to internet (for Claude to reach it)
# Option A: Deploy to Render/Railway/Vercel
# Option B: Use ngrok for testing
ngrok http 5000

# 3. Configure Claude to send POST requests to your endpoint
```

## Tips & Best Practices

1. **Template Design**: Ensure your DOCX template has clear section headers
2. **Section Names**: Keep markdown section names consistent with template
3. **Validation**: Run with `--strict` during development to catch mismatches
4. **Formatting**: Markdown bold (**text**) is preserved in output
5. **Testing**: Use `analyze_docx.py` to understand your template structure

## Troubleshooting

### PDF Generation Fails

If PDF generation fails, DOCX is still created. Common causes:
- Missing dependencies (install `mammoth` and `weasyprint`)
- Complex template formatting (use simpler templates)

### Section Not Populating

1. Check section name matches template (case-insensitive)
2. Run `analyze_docx.py` to see template structure
3. Check validation warnings for mismatches

### Template Formatting Lost

- The generator preserves most formatting, but complex layouts may need adjustment
- Use styles (Normal, List Paragraph, etc.) in your template for best results

## License

MIT

## Contributing

Issues and PRs welcome!
