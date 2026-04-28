#!/usr/bin/env python
"""
Import NWFP group shapefiles into ResourceSite + NWFPGroup models.

Usage
-----
  # Via Django shell:
  python manage.py shell < scripts/import_shapefiles.py

  # Standalone (Django configured via env var or the defaults below):
  python scripts/import_shapefiles.py
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Django setup — must happen before any Django/model imports
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django  # noqa: E402 (import after sys.path manipulation)

django.setup()

# ---------------------------------------------------------------------------
# Application imports (safe after django.setup())
# ---------------------------------------------------------------------------
import fiona  # noqa: E402
from django.contrib.gis.geos import GEOSGeometry  # noqa: E402
from shapely.geometry import mapping, shape  # noqa: E402

from apps.groups.models import NWFPGroup  # noqa: E402
from apps.spatial.models import ResourceSite, SpatialLayer  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SHP_ROOT = Path(
    'E:/Bhutan NWFP Web Marketplace and Management Platform/NWFP Groups Shp Files'
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_or_create_layer(layer_type: str, name: str) -> SpatialLayer:
    """Return an existing SpatialLayer or create one with sensible defaults."""
    layer, created = SpatialLayer.objects.get_or_create(
        name=name,
        defaults={
            'layer_type': layer_type,
            'is_public': True,
            'description': 'Imported from NWFP group shapefiles',
        },
    )
    if created:
        print(f'  [layer] Created layer: "{name}"')
    return layer


def dzongkhag_from_path(path_str: str) -> str:
    """
    Infer a dzongkhag code from any segment of the file path.

    The matching is intentionally loose to handle varied directory naming
    conventions found in the source shapefile archives.
    """
    path_lower = path_str.lower()

    mapping = {
        'bumthang': 'bumthang',
        'chhukha': 'chhukha',
        'gedu': 'chhukha',
        'dagana': 'dagana',
        'gasa': 'gasa',
        'haa': 'haa',
        'lhuentse': 'lhuentse',
        'mongar': 'mongar',
        'paro': 'paro',
        'pemagatshel': 'pemagatshel',
        'punakha': 'punakha',
        'samdrup': 'samdrup_jongkhar',
        'samtse': 'samtse',
        'sarpang': 'sarpang',
        'thimphu': 'thimphu',
        'trashigang': 'trashigang',
        'trashi_yangtse': 'trashi_yangtse',
        'trashiyangtse': 'trashi_yangtse',
        'bumdelling': 'trashi_yangtse',
        'trongsa': 'trongsa',
        'tsirang': 'tsirang',
        'wangdue': 'wangdue',
        'zhemgang': 'zhemgang',
    }

    for keyword, code in mapping.items():
        if keyword in path_lower:
            return code

    return ''


def import_shapefile(shp_path: Path, layer: SpatialLayer) -> int:
    """
    Import all features from *shp_path* into ResourceSite.

    Each shapefile maps to one NWFPGroup (derived from the stem of the
    filename).  Features within a single shapefile that share the same
    name are merged via update_or_create so repeated imports are
    idempotent.

    Returns the number of features imported/updated.
    """
    group_name = shp_path.stem.replace('_', ' ').replace('-', ' ').strip()
    dzongkhag = dzongkhag_from_path(str(shp_path))

    # Get or create the associated NWFPGroup.
    group, group_created = NWFPGroup.objects.get_or_create(
        name=group_name,
        defaults={
            'dzongkhag': dzongkhag,
            'status': 'active',
            'is_deleted': False,
        },
    )
    if group_created:
        print(f'  [group]  Created group: "{group_name}" (dzongkhag={dzongkhag or "unknown"})')
    else:
        print(f'  [group]  Found existing group: "{group_name}"')

    imported = 0

    try:
        with fiona.open(str(shp_path)) as src:
            crs_epsg = None
            if src.crs:
                # Try to read EPSG from the CRS dict (fiona 1.x) or CRS object (fiona 2.x).
                try:
                    from fiona.crs import to_string
                    crs_wkt = to_string(src.crs)
                    # Default to 4326 if we cannot parse; reprojection handled by GEOSGeometry srid
                except Exception:
                    pass
                # Attempt to extract EPSG number for srid
                try:
                    if hasattr(src.crs, 'to_epsg'):
                        crs_epsg = src.crs.to_epsg()
                    elif isinstance(src.crs, dict) and 'init' in src.crs:
                        crs_epsg = int(src.crs['init'].replace('epsg:', ''))
                except Exception:
                    pass

            srid = crs_epsg if crs_epsg else 4326
            print(f'  [crs]    Detected SRID={srid}, feature count={len(src)}')

            for i, feat in enumerate(src):
                geom_raw = feat.get('geometry')
                if geom_raw is None:
                    print(f'  [skip]   Feature {i} has no geometry')
                    continue

                try:
                    shapely_geom = shape(geom_raw)
                    geos_geom = GEOSGeometry(
                        json.dumps(mapping(shapely_geom)), srid=srid
                    )
                    # Reproject to WGS84 (4326) if necessary.
                    if srid != 4326:
                        geos_geom.transform(4326)
                except Exception as geom_err:
                    print(f'  [error]  Feature {i} geometry conversion failed: {geom_err}')
                    continue

                props = dict(feat.get('properties') or {})
                # Use the first non-empty string property as a site name
                # supplement, otherwise fall back to group name.
                site_name = next(
                    (str(v).strip() for v in props.values() if v and str(v).strip()),
                    group_name,
                )

                ResourceSite.objects.update_or_create(
                    name=site_name,
                    group=group,
                    defaults={
                        'geometry': geos_geom,
                        'layer': layer,
                        'site_type': 'collection_site',
                        'dzongkhag': dzongkhag,
                        'source_file': str(shp_path),
                        'status': 'active',
                    },
                )
                imported += 1

    except Exception as exc:
        print(f'  [error]  Failed to open/process {shp_path.name}: {exc}')

    return imported


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run() -> None:
    if not SHP_ROOT.exists():
        print(f'ERROR: Shapefile root directory does not exist: {SHP_ROOT}')
        sys.exit(1)

    layer = get_or_create_layer('group_boundary', 'NWFP Group Boundaries')

    shp_files = sorted(SHP_ROOT.rglob('*.shp'))
    if not shp_files:
        print(f'WARNING: No .shp files found under {SHP_ROOT}')
        return

    print(f'Found {len(shp_files)} shapefile(s) under {SHP_ROOT}\n')

    total = 0
    for shp_file in shp_files:
        print(f'Importing: {shp_file.relative_to(SHP_ROOT)}')
        count = import_shapefile(shp_file, layer)
        total += count
        print(f'  -> {count} feature(s) imported\n')

    print(f'Done.  Total resource sites imported/updated: {total}')


if __name__ == '__main__':
    run()


def import_shapefiles(source_path: str | None = None, dry_run: bool = False, verbosity: int = 1) -> None:
    global SHP_ROOT
    if source_path:
        SHP_ROOT = Path(source_path)
    run()
