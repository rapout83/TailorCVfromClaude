#!/usr/bin/env python3
"""
Webhook API for CV Generation

Receives markdown CV via POST request and generates DOCX + PDF automatically.

Usage:
    python webhook_api.py

API Endpoints:
    POST /generate-cv
        Body: {
            "markdown": "CV content in markdown format",
            "template_name": "template.docx" (optional),
            "output_name": "custom_name" (optional),
            "return_files": true (optional, return files as base64)
        }

    GET /health
        Health check endpoint

    GET /templates
        List available templates
"""

from flask import Flask, request, jsonify, send_file
from pathlib import Path
import tempfile
import shutil
import base64
from datetime import datetime
import traceback
import os

from generate_cv import generate_cv_from_markdown

app = Flask(__name__)

# Configuration
CONFIG = {
    'TEMPLATES_DIR': Path('./templates'),
    'OUTPUT_DIR': Path('./output'),
    'DEFAULT_TEMPLATE': 'Henry Jung_CV_Imperial Brands PLC.docx',
    'MAX_CONTENT_LENGTH': 1 * 1024 * 1024,  # 1MB max request size
}

# Ensure directories exist
CONFIG['TEMPLATES_DIR'].mkdir(exist_ok=True)
CONFIG['OUTPUT_DIR'].mkdir(exist_ok=True)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/templates', methods=['GET'])
def list_templates():
    """List available templates"""
    templates = []

    # Check templates directory
    if CONFIG['TEMPLATES_DIR'].exists():
        templates.extend([
            t.name for t in CONFIG['TEMPLATES_DIR'].glob('*.docx')
        ])

    # Also check current directory
    templates.extend([
        t.name for t in Path('.').glob('*.docx')
        if t.name not in templates
    ])

    return jsonify({
        'templates': templates,
        'default': CONFIG['DEFAULT_TEMPLATE']
    })


@app.route('/generate-cv', methods=['POST'])
def generate_cv():
    """
    Generate CV from markdown

    Request body:
    {
        "markdown": "CV content in markdown",
        "template_name": "template.docx" (optional),
        "output_name": "custom_name" (optional),
        "return_files": true (optional),
        "skip_pdf": false (optional)
    }

    Response:
    {
        "status": "success",
        "files": {
            "docx": "path/to/file.docx",
            "pdf": "path/to/file.pdf"
        },
        "base64": {  // if return_files=true
            "docx": "base64_encoded_content",
            "pdf": "base64_encoded_content"
        }
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'error': 'Request must be JSON'
            }), 400

        data = request.get_json()

        # Validate required fields
        if 'markdown' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing required field: markdown'
            }), 400

        markdown_content = data['markdown']
        template_name = data.get('template_name', CONFIG['DEFAULT_TEMPLATE'])
        output_name = data.get('output_name')
        return_files = data.get('return_files', False)
        skip_pdf = data.get('skip_pdf', False)

        # Find template
        template_path = None
        for search_dir in [CONFIG['TEMPLATES_DIR'], Path('.')]:
            candidate = search_dir / template_name
            if candidate.exists():
                template_path = candidate
                break

        if template_path is None:
            return jsonify({
                'status': 'error',
                'error': f'Template not found: {template_name}',
                'available_templates': list_templates().get_json()['templates']
            }), 404

        # Generate output name if not provided
        if output_name is None:
            output_name = f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create temporary file for markdown
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as tmp_md:
            tmp_md.write(markdown_content)
            tmp_md_path = tmp_md.name

        try:
            # Generate CV
            result = generate_cv_from_markdown(
                markdown_path=tmp_md_path,
                template_path=str(template_path),
                output_dir=str(CONFIG['OUTPUT_DIR']),
                output_name=output_name,
                strict_mode=False,
                skip_pdf=skip_pdf
            )

            # Prepare response
            response_data = {
                'status': 'success',
                'files': {
                    'docx': result['docx'],
                },
                'validation': {
                    'warnings': result['validation'].warnings,
                    'missing_in_template': result['validation'].missing_in_template,
                    'missing_in_markdown': result['validation'].missing_in_markdown
                },
                'timestamp': datetime.now().isoformat()
            }

            if 'pdf' in result:
                response_data['files']['pdf'] = result['pdf']

            # Optionally return file contents as base64
            if return_files:
                response_data['base64'] = {}

                # Read and encode DOCX
                with open(result['docx'], 'rb') as f:
                    response_data['base64']['docx'] = base64.b64encode(f.read()).decode('utf-8')

                # Read and encode PDF if available
                if 'pdf' in result:
                    with open(result['pdf'], 'rb') as f:
                        response_data['base64']['pdf'] = base64.b64encode(f.read()).decode('utf-8')

            return jsonify(response_data), 200

        finally:
            # Cleanup temp markdown file
            try:
                os.unlink(tmp_md_path)
            except:
                pass

    except Exception as e:
        print(f"Error generating CV: {e}")
        traceback.print_exc()

        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc() if app.debug else None
        }), 500


@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download a generated file"""
    file_path = CONFIG['OUTPUT_DIR'] / filename

    if not file_path.exists():
        return jsonify({
            'status': 'error',
            'error': 'File not found'
        }), 404

    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=filename
    )


def main():
    """Start the webhook server"""
    import argparse

    parser = argparse.ArgumentParser(description='CV Generator Webhook API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print("=" * 80)
    print("CV GENERATOR - Webhook API")
    print("=" * 80)
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Health: http://{args.host}:{args.port}/health")
    print(f"Templates: http://{args.host}:{args.port}/templates")
    print(f"Generate: POST http://{args.host}:{args.port}/generate-cv")
    print()
    print("Templates Directory:", CONFIG['TEMPLATES_DIR'].absolute())
    print("Output Directory:", CONFIG['OUTPUT_DIR'].absolute())
    print("=" * 80)
    print()

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
