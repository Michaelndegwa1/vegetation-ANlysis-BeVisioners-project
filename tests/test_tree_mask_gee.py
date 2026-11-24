"""Earth Engine regression test for the Hansen tree mask (needs network + auth).
Run: PYTHONPATH=. python tests/test_tree_mask_gee.py

Guards against the 2026-11-24 bug: lossyear is masked where there was no loss, so the mask collapsed
to the few pixels with later loss (Chyulu 193 pixels instead of ~35,000 at 90 m).
"""
import warnings

warnings.filterwarnings('ignore')
import ee

from canopyledger import config as C
from canopyledger.pipeline import ingest as I

ee.Initialize(project=C.GEE_PROJECT)
h = ee.Image(C.DS_HANSEN)
tc = h.select('treecover2000').unmask(0)
ly = h.select('lossyear').unmask(0)
one = ee.Image.constant(1)
results = []

for site_id, min_expected in (('chyulu_hills_redd', 10000), ('kasigau_ph1_rukinga', 0)):
    feat = I.load_sites([site_id])[0]
    site = ee.Geometry(feat['geometry'], None, False)

    def count(mask):
        return one.updateMask(mask).reduceRegion(
            ee.Reducer.count(), site, scale=90, maxPixels=1e13, tileScale=8).values().get(0)

    year = 2019
    got, ge30, lost_before = ee.List([
        count(I.tree_mask(year, 30)),
        count(tc.gte(30)),
        count(tc.gte(30).And(ly.gt(0)).And(ly.lt(year - 2000))),
    ]).getInfo()
    expected = ge30 - lost_before
    ok = got == expected and got >= min_expected
    print(('PASS ' if ok else 'FAIL ') + f'{site_id}: tree_mask(2019,30)={got}, '
          f'expected (tc>=30 minus lost before 2019) = {expected}, tc>=30 = {ge30}')
    results.append(ok)

print(f'{sum(results)}/{len(results)} passed')
raise SystemExit(0 if all(results) else 1)
