import importlib
import inspect
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


IMPORTERS = {
    'shapefiles': [
        ('scripts.import_shapefiles', 'import_shapefiles'),
    ],
    'csv': [
        ('scripts.import_csv', 'import_csv'),
    ],
    'pdfs': [
        ('scripts.import_pdfs', 'import_pdfs'),
    ],
    'gpkg': [
        ('scripts.import_gpkg', 'import_gpkg'),
    ],
}


class Command(BaseCommand):
    help = 'Import NWFP data from shapefiles, CSV files, PDFs, or GeoPackage files.'

    def add_arguments(self, parser):
        parser.add_argument('--type', required=True, choices=sorted(IMPORTERS))
        parser.add_argument('--path', required=True, help='Path to the file or directory to import.')
        parser.add_argument('--dry-run', action='store_true', help='Validate import input without saving data.')

    def handle(self, *args, **options):
        import_type = options['type']
        source_path = Path(options['path']).expanduser().resolve()
        dry_run = options['dry_run']
        verbosity = options.get('verbosity', 1)

        if not source_path.exists():
            raise CommandError(f'Path does not exist: {source_path}')

        self._validate_source(import_type, source_path)
        importer = self._load_importer(import_type)

        if verbosity:
            mode = 'Validating' if dry_run else 'Importing'
            self.stdout.write(self.style.WARNING(f'{mode} {import_type} from {source_path}'))

        try:
            if dry_run:
                with transaction.atomic():
                    result = self._call_importer(importer, source_path, dry_run=True, verbosity=verbosity)
                    transaction.set_rollback(True)
            else:
                result = self._call_importer(importer, source_path, dry_run=False, verbosity=verbosity)
        except Exception as exc:
            raise CommandError(f'Import failed: {exc}') from exc

        if verbosity:
            self.stdout.write(self.style.SUCCESS('Dry run completed successfully.' if dry_run else 'Import completed successfully.'))
            if result is not None:
                self.stdout.write(str(result))

    def _validate_source(self, import_type, source_path):
        if import_type == 'shapefiles':
            if source_path.is_file() and source_path.suffix.lower() != '.shp':
                raise CommandError('Shapefile imports require a .shp file or a directory containing shapefiles.')
            return

        expected_suffixes = {
            'csv': {'.csv'},
            'pdfs': {'.pdf'},
            'gpkg': {'.gpkg'},
        }
        suffixes = expected_suffixes.get(import_type)
        if source_path.is_file() and suffixes and source_path.suffix.lower() not in suffixes:
            expected = ', '.join(sorted(suffixes))
            raise CommandError(f'{import_type} imports require {expected} files.')

    def _load_importer(self, import_type):
        errors = []
        for module_path, function_name in IMPORTERS[import_type]:
            try:
                module = importlib.import_module(module_path)
                return getattr(module, function_name)
            except (ImportError, AttributeError) as exc:
                errors.append(f'{module_path}.{function_name}: {exc}')
        details = '; '.join(errors)
        raise CommandError(f'No importer found for {import_type}. Checked: {details}')

    def _call_importer(self, importer, source_path, dry_run, verbosity):
        signature = inspect.signature(importer)
        kwargs = {}
        if 'dry_run' in signature.parameters:
            kwargs['dry_run'] = dry_run
        if 'verbosity' in signature.parameters:
            kwargs['verbosity'] = verbosity
        return importer(str(source_path), **kwargs)
