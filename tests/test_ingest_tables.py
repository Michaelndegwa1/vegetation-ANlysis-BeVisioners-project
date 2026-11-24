"""Offline tests for ingest table logic (no Earth Engine). Run: PYTHONPATH=. python tests/test_ingest_tables.py"""
import pandas as pd

from canopyledger.pipeline.ingest import sanity_flags, to_long

BASE = dict(site_id='s', zone='site', year=2023, mask='all', one_count=100)
wide = [
    # normal month
    dict(BASE, month=1, valid_mean=0.9, S2_N_mean=2.5, NDVI_mean=0.4, NDVI_median=0.41, NDVI_p10=0.3,
         NDVI_p90=0.5, NDVI_stdDev=0.05, VV_mean=-11.0),
    # low coverage month
    dict(BASE, month=2, valid_mean=0.2, S2_N_mean=0.3, NDVI_mean=0.35),
    # empty cell (no valid pixels, e.g. Hansen tree mask at Kasigau)
    dict(BASE, mask='tree', month=1, one_count=None, valid_mean=None),
    # yearly coverage row
    dict(BASE, month=0, n_ge2_mean=0.97),
    # dense forest NDVI: allowed for tree mask, flagged for 'all'
    dict(BASE, mask='tree', month=3, valid_mean=1.0, S2_N_mean=3, NDVI_mean=0.86, VV_mean=-9.0),
    dict(BASE, mask='all', month=3, valid_mean=1.0, S2_N_mean=3, NDVI_mean=0.86, VV_mean=-9.0),
]
df = to_long(wide, 'approximate')
results = []


def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    results.append(bool(cond))


check('boundary_quality on every row', (df.boundary_quality == 'approximate').all())
low = df[(df.month == 2) & (df.band == 'NDVI')]
check('low coverage month flagged, not dropped', len(low) == 1 and low.low_coverage.iloc[0] == 1)
check('normal month not flagged', (df[(df.month == 1) & (df['mask'] == 'all') & (df.band == 'NDVI')].low_coverage == 0).all())
none = df[(df['mask'] == 'tree') & (df.month == 1)]
check('empty cell kept as _none row with n_pixels 0', len(none) == 1 and none.band.iloc[0] == '_none' and none.n_pixels.iloc[0] == 0)
cov = df[df.band == '_coverage']
check('coverage row: month 0, stat frac_n_ge2, value kept', len(cov) == 1 and cov.month.iloc[0] == 0 and cov.value.iloc[0] == 0.97)
flags = sanity_flags(df)
check('NDVI 0.86 flagged for mask all', any('site/all' in f and 'NDVI' in f for f in flags))
check('NDVI 0.86 accepted for mask tree', not any('site/tree' in f for f in flags))
check('output sorted and reproducible', df.equals(to_long(list(reversed(wide)), 'approximate')))
check('values rounded to 6 decimals', (df.value.dropna().round(6) == df.value.dropna()).all())
print(f'{sum(results)}/{len(results)} passed')
raise SystemExit(0 if all(results) else 1)
