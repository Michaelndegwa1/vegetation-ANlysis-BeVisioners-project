"""Validate the site registry against docs/specs/01-site-schema.md.

Usage: python -m canopyledger.sites.validate [path]   (default: sites/sites.geojson)
Exit code 1 if any error. Warnings do not fail.
"""
import json
import sys
from pathlib import Path

from pyproj import Geod
from shapely.geometry import shape

DEFAULT_PATH = Path(__file__).with_name('sites.geojson')
SUPPORTED_TYPES = {'REDD+', 'ARR', 'IFM'}
REGISTRY_STATUS = {'confirmed', 'unverified'}
BOUNDARY_QUALITY = {'approximate', 'official'}
BASELINE_METHODS = {'hansen_2000_to_2018', 'landsat_pre2019'}
MIN_RING_M = 2000  # Verra VMD0055 v1.1 minimum leakage-belt width
REQUIRED = ['site_id', 'name', 'project_type', 'registry', 'registry_id', 'registry_id_status',
            'funding_start', 'monitoring_start', 'baseline_method', 'boundary_quality',
            'boundary_source', 'position_error_km', 'area_ha_documented',
            'area_ha_documented_source', 'leakage_buffer_m', 'leakage_rings_m',
            'mask_protected_in_ring']
GEOD = Geod(ellps='WGS84')


def polygon_area_ha(geom):
    """Geodesic area in hectares."""
    return abs(GEOD.geometry_area_perimeter(geom)[0]) / 1e4


def validate(path=DEFAULT_PATH):
    errors, warnings = [], []
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    ids = set()
    for i, f in enumerate(data['features']):
        p = f['properties']
        sid = p.get('site_id', f'feature[{i}]')
        e = lambda m: errors.append(f'{sid}: {m}')
        w = lambda m: warnings.append(f'{sid}: {m}')

        for k in REQUIRED:
            if k not in p:
                e(f'missing field {k}')
        if sid in ids:
            e('duplicate site_id')
        ids.add(sid)

        geom = shape(f['geometry'])
        if geom.geom_type not in ('Polygon', 'MultiPolygon'):
            e(f'geometry type {geom.geom_type}')
        if not geom.is_valid:
            e('invalid geometry')
        minx, miny, maxx, maxy = geom.bounds
        if not (33.5 <= minx and maxx <= 42 and -5 <= miny and maxy <= 5.5):
            e(f'outside Kenya box: {geom.bounds}')

        if p.get('project_type') not in SUPPORTED_TYPES:
            e(f"unsupported project_type {p.get('project_type')!r}")
        if p.get('registry_id_status') not in REGISTRY_STATUS:
            e('bad registry_id_status')
        if p.get('registry_id_status') == 'confirmed' and p.get('registry_id') is None:
            e('registry_id_status confirmed but registry_id is null')
        if p.get('boundary_quality') not in BOUNDARY_QUALITY:
            e('bad boundary_quality')
        if p.get('baseline_method') not in BASELINE_METHODS:
            e('bad baseline_method')
        if p.get('boundary_quality') == 'approximate' and not isinstance(
                p.get('position_error_km'), (int, float)):
            e('approximate boundary needs numeric position_error_km')
        rings = p.get('leakage_rings_m')
        if rings is not None:
            if (not isinstance(rings, list) or not rings
                    or not all(isinstance(r, int) and not isinstance(r, bool) for r in rings)):
                e('leakage_rings_m must be a non-empty list of integers (metres)')
            else:
                if rings != sorted(set(rings)):
                    e('leakage_rings_m must be strictly increasing')
                if min(rings) < MIN_RING_M:
                    e(f'leakage_rings_m has a ring below the {MIN_RING_M} m minimum')
                if p.get('leakage_buffer_m') not in rings:
                    e('leakage_rings_m must contain leakage_buffer_m')
        if 'mask_protected_in_ring' in p and not isinstance(p['mask_protected_in_ring'], bool):
            e('mask_protected_in_ring must be true or false')
        if p.get('funding_start') is None and not p.get('funding_start_note'):
            w('funding_start null without funding_start_note')

        ha = polygon_area_ha(geom)
        if 'area_ha_polygon' in p and abs(p['area_ha_polygon'] - ha) / ha > 0.01:
            e(f"area_ha_polygon {p['area_ha_polygon']} != recomputed {ha:.0f}")
        doc = p.get('area_ha_documented')
        if doc:
            diff = abs(ha - doc) / doc
            if diff > 0.30:
                e(f'polygon {ha:.0f} ha vs documented {doc:.0f} ha ({diff:.0%})')
            elif diff > 0.15:
                w(f'polygon {ha:.0f} ha vs documented {doc:.0f} ha ({diff:.0%})')
    return errors, warnings


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    errs, warns = validate(path)
    for m in warns:
        print('WARN ', m)
    for m in errs:
        print('ERROR', m)
    print(f'{len(errs)} error(s), {len(warns)} warning(s)')
    sys.exit(1 if errs else 0)
