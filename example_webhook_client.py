#!/usr/bin/env python3
"""
Example Webhook Client - Shows how to send CV markdown to the webhook API

This demonstrates how Claude (or any other client) can send markdown CV
to the webhook for automatic processing.
"""

import requests
import json


def send_cv_to_webhook(markdown_content: str, webhook_url: str = "http://localhost:5000/generate-cv"):
    """
    Send markdown CV to webhook for processing

    Args:
        markdown_content: CV in markdown format
        webhook_url: URL of the webhook endpoint

    Returns:
        Response from webhook
    """
    print("📤 Sending CV to webhook...")
    print(f"   Endpoint: {webhook_url}")

    payload = {
        "markdown": markdown_content,
        "template_name": "Henry Jung_CV_Imperial Brands PLC.docx",
        "output_name": "Generated_CV",
        "return_files": False,  # Set to True to get base64 encoded files in response
        "skip_pdf": False
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(f"   Status: {result['status']}")
            print(f"\n📁 Generated Files:")
            print(f"   DOCX: {result['files'].get('docx')}")
            if 'pdf' in result['files']:
                print(f"   PDF:  {result['files'].get('pdf')}")

            if result.get('validation', {}).get('warnings'):
                print(f"\n⚠️  Warnings:")
                for warning in result['validation']['warnings']:
                    print(f"   - {warning}")

            return result
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            return None

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to webhook")
        print("   Make sure the webhook server is running:")
        print("   python webhook_api.py")
        return None

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


def main():
    """Example usage"""
    print("=" * 80)
    print("CV GENERATOR - Webhook Client Example")
    print("=" * 80)
    print()

    # Load example markdown CV
    markdown_file = "Henry_Jung_CV_Imperial_Brands_Head_Enterprise_Data_Platforms.md"

    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find {markdown_file}")
        print("   Using dummy content instead...")
        markdown_content = """# JOHN DOE

**Software Engineer**

Experienced software engineer with 10 years of experience...

---

## PROFESSIONAL EXPERIENCE

### Senior Software Engineer | Tech Company | 2020-Present

- Built scalable systems
- Led team of 5 engineers

---

## EDUCATION

**BS Computer Science** | University Name
"""

    # Send to webhook
    result = send_cv_to_webhook(markdown_content)

    if result:
        print("\n" + "=" * 80)
        print("✅ CV generated successfully via webhook!")
        print("=" * 80)


if __name__ == "__main__":
    main()
