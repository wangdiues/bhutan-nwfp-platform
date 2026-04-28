#!/usr/bin/env python
"""
Validate and import CSV harvest data into the HarvestBatch model.

Expected CSV columns (header row required, case-insensitive):
  species, scientific_name, harvest_date, quantity, unit,
  site_name, latitude, longitude, collector_count, notes, group_name

Validation rules
----------------
  - All required columns must be present.
  - harvest_date must be parseable as YYYY-MM-DD.
  - latitude must be in the range [26, 29]  (Bhutan bounding box).
  - longitude must be in the range [88, 93].
  - quantity must be > 0.
  - group_name must match an existing NWFPGroup (warning, not error).

Usage
-----
  python scripts/import_csv.py path/to/harvest_data.csv
  python scripts/import_csv.py path/to/harvest_data.csv --dry-run
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django  # noqa: E402

django.setup()

from apps.groups.models import NWFPGroup  # noqa: E402
from apps.inventory.models import HarvestBatch  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    'species',
    'scientific_name',
    'harvest_date',
    'quantity',
    'unit',
    'site_name',
    'latitude',
    'longitude',
    'collector_count',
    'notes',
    'group_name',
]

# Bhutan bounding box (approximate)
BHUTAN_LAT_MIN = 26.0
BHUTAN_LAT_MAX = 29.5
BHUTAN_LON_MIN = 88.0
BHUTAN_LON_MAX = 93.0


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class RowValidationError(Exception):
    pass


def parse_date(value: str, field: str) -> datetime.date:
    value = value.strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise RowValidationError(
        f'{field}: "{value}" is not a valid date (expected YYYY-MM-DD).'
    )


def parse_float(value: str, field: str) -> float:
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        raise RowValidationError(f'{field}: "{value}" is not a valid number.')


def parse_int(value: str, field: str) -> int:
    try:
        return int(str(value).strip())
    except (ValueError, AttributeError):
        raise RowValidationError(f'{field}: "{value}" is not a valid integer.')


def validate_row(row: dict, row_number: int) -> dict:
    """
    Validate a single CSV row.

    Returns a cleaned data dict suitable for HarvestBatch.objects.create().
    Raises RowValidationError with a descriptive message on failure.
    """
    errors = []

    # --- harvest_date ---
    try:
        harvest_date = parse_date(row.get('harvest_date', ''), 'harvest_date')
    except RowValidationError as e:
        errors.append(str(e))
        harvest_date = None

    # --- quantity ---
    try:
        quantity = parse_float(row.get('quantity', ''), 'quantity')
        if quantity <= 0:
            errors.append('quantity: must be greater than zero.')
    except RowValidationError as e:
        errors.append(str(e))
        quantity = None

    # --- latitude ---
    lat_raw = row.get('latitude', '').strip()
    latitude = None
    if lat_raw:
        try:
            latitude = parse_float(lat_raw, 'latitude')
            if not (BHUTAN_LAT_MIN <= latitude <= BHUTAN_LAT_MAX):
                errors.append(
                    f'latitude: {latitude} is outside Bhutan bounds '
                    f'({BHUTAN_LAT_MIN}–{BHUTAN_LAT_MAX}°N).'
                )
        except RowValidationError as e:
            errors.append(str(e))

    # --- longitude ---
    lon_raw = row.get('longitude', '').strip()
    longitude = None
    if lon_raw:
        try:
            longitude = parse_float(lon_raw, 'longitude')
            if not (BHUTAN_LON_MIN <= longitude <= BHUTAN_LON_MAX):
                errors.append(
                    f'longitude: {longitude} is outside Bhutan bounds '
                    f'({BHUTAN_LON_MIN}–{BHUTAN_LON_MAX}°E).'
                )
        except RowValidationError as e:
            errors.append(str(e))

    # --- collector_count ---
    cc_raw = row.get('collector_count', '0').strip() or '0'
    try:
        collector_count = parse_int(cc_raw, 'collector_count')
    except RowValidationError as e:
        errors.append(str(e))
        collector_count = 0

    # --- species (required non-empty) ---
    species = row.get('species', '').strip()
    if not species:
        errors.append('species: must not be empty.')

    # --- unit (required non-empty) ---
    unit = row.get('unit', '').strip()
    if not unit:
        errors.append('unit: must not be empty.')

    if errors:
        raise RowValidationError('; '.join(errors))

    return {
        'species': species,
        'scientific_name': row.get('scientific_name', '').strip(),
        'harvest_date': harvest_date,
        'quantity_harvested': quantity,
        'quantity_unit': unit,
        'site_name': row.get('site_name', '').strip(),
        'latitude': latitude,
        'longitude': longitude,
        'collector_count': collector_count,
        'notes': row.get('notes', '').strip(),
        'group_name': row.get('group_name', '').strip(),
    }


# ---------------------------------------------------------------------------
# Group resolution
# ---------------------------------------------------------------------------

# Cache group lookups to avoid repeated DB queries.
_group_cache: dict[str, NWFPGroup | None] = {}


def resolve_group(name: str) -> NWFPGroup | None:
    if name in _group_cache:
        return _group_cache[name]
    try:
        group = NWFPGroup.objects.get(name__iexact=name)
    except NWFPGroup.DoesNotExist:
        group = None
    _group_cache[name] = group
    return group


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------


def run_import(csv_path: str, dry_run: bool = False) -> None:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f'ERROR: File not found: {csv_file}')
        sys.exit(1)

    # Determine error log path.
    error_log_path = csv_file.with_suffix('.errors.log')

    imported_count = 0
    skipped_count = 0
    unmatched_groups: list[str] = []
    error_lines: list[str] = []

    with open(csv_file, newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)

        # Normalise header names to lowercase and strip whitespace.
        if reader.fieldnames is None:
            print('ERROR: CSV file appears to be empty or has no header row.')
            sys.exit(1)

        normalised_fieldnames = [f.strip().lower() for f in reader.fieldnames]
        reader.fieldnames = normalised_fieldnames

        # Check all required columns are present.
        missing = [col for col in REQUIRED_COLUMNS if col not in normalised_fieldnames]
        if missing:
            print(
                'ERROR: CSV is missing required column(s): '
                + ', '.join(f'"{c}"' for c in missing)
            )
            print(f'Expected: {REQUIRED_COLUMNS}')
            print(f'Found:    {normalised_fieldnames}')
            sys.exit(1)

        print(f'CSV file: {csv_file}')
        print(f'Columns:  {normalised_fieldnames}')
        print(f'Dry-run:  {dry_run}\n')

        for row_number, row in enumerate(reader, start=2):  # row 1 is the header
            # Normalise keys.
            row = {k.strip().lower(): (v or '').strip() for k, v in row.items() if k}

            try:
                cleaned = validate_row(row, row_number)
            except RowValidationError as exc:
                msg = f'Row {row_number}: SKIPPED — {exc}'
                print(f'  {msg}')
                error_lines.append(msg)
                skipped_count += 1
                continue

            # Resolve group.
            group = resolve_group(cleaned['group_name'])
            if group is None:
                note = (
                    f'Row {row_number}: WARNING — group "{cleaned["group_name"]}" '
                    'not found in database; row skipped because HarvestBatch requires a group.'
                )
                print(f'  {note}')
                error_lines.append(note)
                if cleaned['group_name'] not in unmatched_groups:
                    unmatched_groups.append(cleaned['group_name'])
                skipped_count += 1
                continue

            if not dry_run:
                HarvestBatch.objects.create(
                    group=group,
                    species=cleaned['species'],
                    scientific_name=cleaned['scientific_name'],
                    harvest_date=cleaned['harvest_date'],
                    quantity_harvested=cleaned['quantity_harvested'],
                    quantity_unit=cleaned['quantity_unit'],
                    site_name=cleaned['site_name'],
                    latitude=cleaned['latitude'],
                    longitude=cleaned['longitude'],
                    collector_count=cleaned['collector_count'],
                    notes=cleaned['notes'],
                    uploaded_via_csv=True,
                    source_file=str(csv_file),
                )

            imported_count += 1

    # Write error log if there were any issues.
    if error_lines:
        with open(error_log_path, 'w', encoding='utf-8') as ef:
            ef.write('\n'.join(error_lines) + '\n')
        print(f'\nError/warning log written to: {error_log_path}')

    # Final summary.
    print('\n' + '=' * 50)
    print(f'Import summary{"  [DRY RUN - nothing written]" if dry_run else ""}')
    print(f'  Rows imported : {imported_count}')
    print(f'  Rows skipped  : {skipped_count}')
    if unmatched_groups:
        print(f'  Unmatched groups ({len(unmatched_groups)}): {unmatched_groups}')
    print('=' * 50)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Import harvest data from a CSV file into HarvestBatch.'
    )
    parser.add_argument('csv_file', help='Path to the CSV file to import.')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate the CSV without writing any records to the database.',
    )
    args = parser.parse_args()
    run_import(args.csv_file, dry_run=args.dry_run)


def import_csv(source_path: str, dry_run: bool = False, verbosity: int = 1) -> None:
    run_import(source_path, dry_run=dry_run)


if __name__ == '__main__':
    main()
