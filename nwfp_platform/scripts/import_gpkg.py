#!/usr/bin/env python
"""
Import NWFP group geometries from a GeoPackage file into ResourceSite + NWFPGroup models.

The script reads every layer inside the GeoPackage and bulk-imports its
features.  Layers are mapped to SpatialLayer objects using the GeoPackage
layer name.

Usage
-----
  python scripts/import_gpkg.py
  # or via Django shell:
  python manage.py shell < scripts/import_gpkg.py
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django  # noqa: E402

django.setup()

# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------
import fiona  # noqa: E402
from django.contrib.gis.geos import GEOSGeometry  # noqa: E402
from django.db import transaction  # noqa: E402
from shapely.geometry import mapping, shape  # noqa: E402

from apps.groups.models import NWFPGroup  # noqa: E402
from apps.spatial.models import ResourceSite, SpatialLayer  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GPKG_ROOT = Path(
    'E:/Bhutan NWFP Web Marketplace and Management Platform/'
    'nwfp_groups_gpkeg_files/NWFP_groups_merged.gpkg'
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Reuse the same dzongkhag inference logic from import_shapefiles.
_DZONGKHAG_KEYWORDS = {
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


def dzongkhag_from_name(name: str) -> str:
    name_lower = name.lower()
    for keyword, code in _DZONGKHAG_KEYWORDS.items():
        if keyword in name_lower:
            return code
    return ''


def get_or_create_spatial_layer(layer_name: str) -> SpatialLayer:
    layer, created = SpatialLayer.objects.get_or_create(
        name=layer_name,
        defaults={
            'layer_type': 'group_boundary',
            'is_public': True,
            'description': f'Imported from GeoPackage layer "{layer_name}"',
        },
    )
    if created:
        print(f'  [layer] Created SpatialLayer: "{layer_name}"')
    return layer


def get_srid_from_crs(crs) -> int:
    """Best-effort EPSG extraction from a fiona CRS object."""
    if crs is None:
        return 4326
    try:
        if hasattr(crs, 'to_epsg'):
            epsg = crs.to_epsg()
            if epsg:
                return int(epsg)
    except Exception:
        pass
    try:
        if isinstance(crs, dict) and 'init' in crs:
            return int(crs['init'].lower().replace('epsg:', ''))
    except Exception:
        pass
    return 4326


# ---------------------------------------------------------------------------
# Main import function
# ---------------------------------------------------------------------------


@transaction.atomic
def import_gpkg_layer(layer_name: str, spatial_layer: SpatialLayer, srid: int) -> int:
    """
    Import all features from a single GeoPackage layer.

    Returns the count of features imported or updated.
    """
    dzongkhag = dzongkhag_from_name(layer_name)
    group_name = layer_name.replace('_', ' ').strip()

    group, group_created = NWFPGroup.objects.get_or_create(
        name=group_name,
        defaults={
            'dzongkhag': dzongkhag,
            'status': 'active',
            'is_deleted': False,
        },
    )
    if group_created:
        print(f'    [group] Created: "{group_name}" (dzongkhag={dzongkhag or "unknown"})')

    imported = 0
    with fiona.open(str(GPKG_ROOT), layer=layer_name) as src:
        for i, feat in enumerate(src):
            geom_raw = feat.get('geometry')
            if geom_raw is None:
                continue

            try:
                shapely_geom = shape(geom_raw)
                geos_geom = GEOSGeometry(json.dumps(mapping(shapely_geom)), srid=srid)
                if srid != 4326:
                    geos_geom.transform(4326)
            except Exception as exc:
                print(f'    [error] Feature {i} geometry error: {exc}')
                continue

            props = dict(feat.get('properties') or {})
            site_name = next(
                (str(v).strip() for v in props.values() if v and str(v).strip()),
                group_name,
            )

            ResourceSite.objects.update_or_create(
                name=site_name,
                group=group,
                defaults={
                    'geometry': geos_geom,
                    'layer': spatial_layer,
                    'site_type': 'collection_site',
                    'dzongkhag': dzongkhag,
                    'source_file': str(GPKG_ROOT),
                    'status': 'active',
                },
            )
            imported += 1

    return imported


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run() -> None:
    if not GPKG_ROOT.exists():
        print(f'ERROR: GeoPackage file not found: {GPKG_ROOT}')
        sys.exit(1)

    print(f'GeoPackage: {GPKG_ROOT}')

    # Enumerate all layers in the GeoPackage.
    layer_names = fiona.listlayers(str(GPKG_ROOT))
    print(f'Found {len(layer_names)} layer(s):\n')

    total_features = 0
    summary_rows = []

    for layer_name in layer_names:
        # Open the layer briefly to get metadata.
        with fiona.open(str(GPKG_ROOT), layer=layer_name) as src:
            feature_count = len(src)
            srid = get_srid_from_crs(src.crs)
            geometry_type = src.schema.get('geometry', 'Unknown')

        print(
            f'  Layer: "{layer_name}"  |  features={feature_count}'
            f'  |  geometry={geometry_type}  |  SRID={srid}'
        )

        spatial_layer = get_or_create_spatial_layer(layer_name)
        imported = import_gpkg_layer(layer_name, spatial_layer, srid)
        total_features += imported
        summary_rows.append((layer_name, feature_count, imported))
        print(f'    -> {imported} site(s) imported/updated\n')

    # Summary table.
    print('=' * 60)
    print(f'{"Layer":<40} {"Features":>8} {"Imported":>8}')
    print('-' * 60)
    for row in summary_rows:
        print(f'{row[0]:<40} {row[1]:>8} {row[2]:>8}')
    print('=' * 60)
    print(f'Total features imported/updated: {total_features}')


if __name__ == '__main__':
    run()


def import_gpkg(source_path: str | None = None, dry_run: bool = False, verbosity: int = 1) -> None:
    global GPKG_ROOT
    if source_path:
        GPKG_ROOT = Path(source_path)
    run()
