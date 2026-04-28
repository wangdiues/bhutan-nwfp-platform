import json


def validate_bhutan_coords(lat, lon) -> bool:
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError):
        return False
    return 26.0 <= latitude <= 29.0 and 88.0 <= longitude <= 93.5


def group_to_geojson(group) -> dict:
    sites = list(group.resource_sites.all()) if getattr(group, 'pk', None) else []
    geometries = [_geometry_to_geojson(site.geometry) for site in sites if getattr(site, 'geometry', None)]
    geometry = {'type': 'GeometryCollection', 'geometries': geometries}

    if not geometries:
        lat = getattr(group, 'headquarters_lat', None)
        lon = getattr(group, 'headquarters_lon', None)
        geometry = {'type': 'Point', 'coordinates': [float(lon), float(lat)]} if validate_bhutan_coords(lat, lon) else None

    return {
        'type': 'Feature',
        'id': str(getattr(group, 'pk', '')),
        'geometry': geometry,
        'properties': {
            'name': getattr(group, 'name', ''),
            'slug': getattr(group, 'slug', ''),
            'dzongkhag': getattr(group, 'dzongkhag', ''),
            'gewog': getattr(group, 'gewog', ''),
            'village': getattr(group, 'village', ''),
            'status': getattr(group, 'status', ''),
            'total_members': getattr(group, 'total_members', 0),
            'resource_site_count': len(sites),
        },
    }


def sites_to_geojson(queryset) -> dict:
    return {
        'type': 'FeatureCollection',
        'features': [_site_to_feature(site) for site in queryset],
    }


def _site_to_feature(site) -> dict:
    group = getattr(site, 'group', None)
    return {
        'type': 'Feature',
        'id': str(getattr(site, 'pk', '')),
        'geometry': _geometry_to_geojson(getattr(site, 'geometry', None)),
        'properties': {
            'name': getattr(site, 'name', ''),
            'site_type': getattr(site, 'site_type', ''),
            'species': getattr(site, 'species', ''),
            'area_ha': getattr(site, 'area_ha', None),
            'elevation_m': getattr(site, 'elevation_m', None),
            'dzongkhag': getattr(site, 'dzongkhag', ''),
            'status': getattr(site, 'status', ''),
            'group_id': str(getattr(group, 'pk', '')) if group else '',
            'group_name': getattr(group, 'name', '') if group else '',
        },
    }


def _geometry_to_geojson(geometry):
    if geometry is None:
        return None
    return json.loads(geometry.geojson)
