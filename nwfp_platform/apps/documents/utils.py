from pathlib import Path

from PyPDF2 import PdfReader


MAX_UPLOAD_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    '.pdf',
    '.csv',
    '.txt',
    '.doc',
    '.docx',
    '.xls',
    '.xlsx',
    '.jpg',
    '.jpeg',
    '.png',
    '.shp',
    '.shx',
    '.dbf',
    '.prj',
    '.cpg',
    '.gpkg',
    '.geojson',
    '.json',
}

FILE_TYPES = {
    '.pdf': 'pdf',
    '.csv': 'csv',
    '.txt': 'text',
    '.doc': 'word',
    '.docx': 'word',
    '.xls': 'spreadsheet',
    '.xlsx': 'spreadsheet',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.shp': 'shapefile',
    '.shx': 'shapefile_index',
    '.dbf': 'shapefile_table',
    '.prj': 'projection',
    '.cpg': 'codepage',
    '.gpkg': 'geopackage',
    '.geojson': 'geojson',
    '.json': 'json',
}


def extract_pdf_text(file_path) -> str:
    try:
        reader = PdfReader(str(file_path))
        return '\n'.join(page.extract_text() or '' for page in reader.pages).strip()
    except Exception:
        return ''


def detect_file_type(filename) -> str:
    extension = Path(filename or '').suffix.lower()
    return FILE_TYPES.get(extension, 'unknown')


def validate_file_upload(file) -> tuple[bool, str]:
    if not file:
        return False, 'No file was provided.'

    size = getattr(file, 'size', 0) or 0
    if size >= MAX_UPLOAD_SIZE:
        return False, 'File size must be less than 50MB.'

    extension = Path(getattr(file, 'name', '')).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
        return False, f'Unsupported file type. Allowed extensions: {allowed}.'

    return True, ''
