#!/usr/bin/env python
"""
Import management-plan PDFs into the Document model.

Usage:
  python scripts/import_pdfs.py ../management_plans_nwfp
  python manage.py import_data --type pdfs --path ../management_plans_nwfp
"""

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django  # noqa: E402

django.setup()

from django.core.files import File  # noqa: E402

from apps.documents.models import Document  # noqa: E402
from apps.groups.models import NWFPGroup  # noqa: E402


def extract_pdf_text(path: Path) -> str:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return ''

    try:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or '').strip() for page in reader.pages[:20]]
        return '\n\n'.join(page for page in pages if page)
    except Exception:
        return ''


def infer_group(path: Path):
    stem = path.stem.lower()
    for group in NWFPGroup.objects.filter(is_deleted=False).only('id', 'name'):
        tokens = [token for token in group.name.lower().replace('-', ' ').split() if len(token) > 3]
        if tokens and any(token in stem for token in tokens[:4]):
            return group
    return None


def iter_pdfs(source: Path):
    if source.is_file():
        if source.suffix.lower() == '.pdf':
            yield source
        return
    yield from sorted(source.rglob('*.pdf'))


def import_pdfs(source_path: str, dry_run: bool = False, verbosity: int = 1):
    source = Path(source_path)
    imported = 0
    skipped = 0

    for pdf_path in iter_pdfs(source):
        group = infer_group(pdf_path)
        title = pdf_path.stem.replace('_', ' ').strip()
        extracted_text = extract_pdf_text(pdf_path)

        if dry_run:
            imported += 1
            if verbosity:
                print(f'[dry-run] {pdf_path.name} -> {group or "unlinked"}')
            continue

        with pdf_path.open('rb') as handle:
            document, created = Document.objects.get_or_create(
                title=title,
                group=group,
                defaults={
                    'file_type': 'pdf',
                    'status': 'processed' if extracted_text else 'pending',
                    'extracted_text': extracted_text,
                },
            )
            if created:
                document.file.save(pdf_path.name, File(handle), save=True)
                imported += 1
            else:
                skipped += 1

    if verbosity:
        print(f'PDF import complete: imported={imported}, skipped={skipped}')
    return {'imported': imported, 'skipped': skipped}


def main():
    parser = argparse.ArgumentParser(description='Import management-plan PDFs.')
    parser.add_argument('path')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    import_pdfs(args.path, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
