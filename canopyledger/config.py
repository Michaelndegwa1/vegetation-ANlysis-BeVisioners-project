"""Central configuration (docs/specs/00-architecture.md: config lives in one place)."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITES_FILE = REPO_ROOT / 'canopyledger' / 'sites' / 'sites.geojson'
STATS_DIR = REPO_ROOT / 'data' / 'processed' / 'stats'

GEE_PROJECT = 'premium-episode-423509-g8'
DRIVE_FOLDER = 'canopyledger_stats'

# Datasets (existence verified 2026-11-24, docs/verification-gee.md)
DS_S2 = 'COPERNICUS/S2_SR_HARMONIZED'
DS_S2_CLOUD = 'COPERNICUS/S2_CLOUD_PROBABILITY'
DS_S1 = 'COPERNICUS/S1_GRD'
DS_HANSEN = 'UMD/hansen/global_forest_change_2025_v1_13'   # 2024_v1_12 is deprecated
DS_WORLDCOVER = 'ESA/WorldCover/v200'                       # 2021 static map; classes 10 tree, 20 shrub

# Cloud masking (tested on 2023 Mau box)
CLOUD_PROB_MAX = 40      # s2cloudless probability (%) above which a pixel is masked
CLOUD_DILATE_M = 100     # grow the cloud mask

# Ingest statistics
STATS_SCALE_M = 30       # reduceRegion scale; fall back to 60 if Chyulu is too slow
TILE_SCALE = 4
LOW_COVERAGE_FRAC = 0.5  # months with valid_frac below this are flagged, never dropped
TREE_COVER_MIN_DEFAULT = 30   # Hansen treecover2000 % threshold; per-site tuning pending (spec 03, Q2)

BANDS_OUT = ['NDVI', 'EVI', 'NDWI', 'VV', 'VH', 'VH_VV']
S1_FIRST_YEAR = 2015     # S1_GRD exists from 2014-10; use from 2015

# Sanity bounds for outputs (to be tightened after the first run)
SANITY = {'NDVI': (0.1, 0.8), 'VV': (-18.0, -6.0)}

SPEC_VERSION = 'ingest-spec v0.2'
