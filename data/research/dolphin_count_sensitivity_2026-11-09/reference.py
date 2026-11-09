"""Reuse the sealed completed banks by path/SHA; never copy raw outcomes."""
import csv
from pathlib import Path
from cases import ROOT, UPPER_BULK

DISCOVERY = ROOT/'research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1/cases'
HIGH = Path('/tmp/FishSim_High_Count_Extension_2026-11-09/full_36T_v1/cases')
UPPER_CASES = UPPER_BULK/'full_36T_v1/cases'
MAP = UPPER_BULK/'full_36T_v1/analysis_final/case_outcomes.csv'
MAP_AUDIT = MAP.parent/'analysis_audit.json'
MAP_REVIEW = UPPER_BULK/'independent_complete_map_review.json'


def reference_name(seed, h, g, dolphins=12):
    policy = f'H{h:g}_G{g}' if dolphins else f'Gonly{g}'
    presence = ('D' if dolphins else '')+('G' if g else '')
    return f's{seed}_{policy}_{presence}_c61001'


def reference_path(seed, h, g, dolphins=12):
    base = DISCOVERY if g <= 6 else HIGH if g <= 18 else UPPER_CASES
    return base/reference_name(seed, h, g, dolphins)


def read_map():
    with MAP.open(newline='') as handle:
        return list(csv.DictReader(handle))
