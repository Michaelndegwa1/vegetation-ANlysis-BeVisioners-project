"""Tests for canopyledger.sites.validate (run: PYTHONPATH=. python tests/test_validate_sites.py)."""
import copy
import json
import tempfile
from pathlib import Path

from canopyledger.sites.validate import DEFAULT_PATH, validate

GOOD = json.loads(Path(DEFAULT_PATH).read_text(encoding='utf-8'))


def run(mutator):
    d = copy.deepcopy(GOOD)
    mutator(d['features'])
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / 'x.geojson'
        p.write_text(json.dumps(d), encoding='utf-8')
        return validate(p)[0]


def expect(name, mutator, fragment):
    errs = run(mutator)
    ok = any(fragment in e for e in errs)
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  errors={errs}'))
    return ok


good_errs = validate()[0]
good_ok = not good_errs
print(('PASS ' if good_ok else 'FAIL ') + 'current sites.geojson has no errors', good_errs or '')
results = [
    good_ok,
    expect('unsupported type', lambda f: f[0]['properties'].update(project_type='soil'), 'unsupported project_type'),
    expect('duplicate site_id', lambda f: f[1]['properties'].update(site_id=f[0]['properties']['site_id']), 'duplicate'),
    expect('missing rings field', lambda f: f[0]['properties'].pop('leakage_rings_m'), 'missing field leakage_rings_m'),
    expect('missing mask flag', lambda f: f[0]['properties'].pop('mask_protected_in_ring'), 'missing field mask_protected_in_ring'),
    expect('ring below 2 km', lambda f: f[0]['properties'].update(leakage_rings_m=[1000, 2000, 5000]), 'below the 2000 m minimum'),
    expect('rings not increasing', lambda f: f[0]['properties'].update(leakage_rings_m=[5000, 2000, 10000]), 'strictly increasing'),
    expect('rings missing primary buffer', lambda f: f[0]['properties'].update(leakage_rings_m=[3000, 5000]), 'must contain leakage_buffer_m'),
    expect('rings wrong type', lambda f: f[0]['properties'].update(leakage_rings_m='2000'), 'non-empty list of integers'),
    expect('mask flag not bool', lambda f: f[0]['properties'].update(mask_protected_in_ring='yes'), 'must be true or false'),
    expect('bad baseline method', lambda f: f[0]['properties'].update(baseline_method='gedi'), 'bad baseline_method'),
    expect('approximate without numeric error', lambda f: f[1]['properties'].update(position_error_km=None), 'numeric position_error_km'),
]
print(f'{sum(map(bool, results))}/{len(results)} passed')
raise SystemExit(0 if all(results) else 1)
