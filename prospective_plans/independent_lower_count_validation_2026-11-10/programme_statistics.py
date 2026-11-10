"""Additional predeclared four-endpoint family; production activation is closed.

The pure arithmetic is tested on synthetic complete rows. Actual programme
analysis requires both independent FINAL receipts, including a future reviewed
lower-count auditor source which has deliberately not yet been bound.
"""
import importlib.util
import csv
import math
from pathlib import Path
import numpy as np
from common import HERE, read, sha
from evidence import PARENT, PARENT_BULK, ExecutionClosed, validate_parent_final_review
from cases import BULK
import secondary_statistics as lower

T_CRITICAL = 2.8366274760941357
CONFIDENCE = .9875
PARENT_STATS_SHA256 = 'f99252aeda8dee74b37ecf9cf1aeb86df2da444e81e6172555f409ccc2f6d723'
LOWER_FINAL_AUDITOR_SHA256 = None  # Future independent source review must bind it.
COLUMNS = ('fine_H1_G36_D', 'fine_H1_G36_G', 'fine_H2_G12_D', 'fine_H2_G12_G')


def _parent_module():
    path = PARENT/'validation_statistics.py'
    if sha(path) != PARENT_STATS_SHA256:
        raise RuntimeError('Original primary statistics source changed')
    spec = importlib.util.spec_from_file_location('_lower_followup_frozen_primary_statistics', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _calculate(primary_rows, lower_rows):
    """Pure integer-first arithmetic; callers must enforce production gates."""
    primary = _parent_module()._normalise(primary_rows)
    followup = lower._normalise(lower_rows)
    if {r['case_id'] for r in primary} & {r['case_id'] for r in followup}:
        raise ValueError('All384 case identities must be distinct; setting-specific controls cannot be reused')
    tables = [{(r['school_seed'], r['replicate_label'], r['grid'], r['presence']): r for r in rows}
              for rows in (primary, followup)]
    denominators = np.asarray([24, 72, 24, 24], dtype=np.int64)
    integer_schools = []
    for school in lower.SCHOOL_SEEDS:
        row = []
        for index in tables:
            for species in ('D', 'G'):
                row.append(sum(index[school, label, 'fine', 'DG'][species+'_captures']
                               - index[school, label, 'fine', species][species+'_captures']
                               for label in lower.REPLICATE_LABELS))
        integer_schools.append(row)
    counts = np.asarray(integer_schools, dtype=np.int64)
    points = counts/denominators
    summaries = {}
    for j, name in enumerate(COLUMNS):
        mean = int(counts[:, j].sum())/(16*int(denominators[j]))
        sd = float(np.std(points[:, j], ddof=1)); se = sd/4
        summaries[name] = dict(mean=mean, school_sd=sd, se=se, n_schools=16, df=15,
                               student_t_98_75_ci=[mean-T_CRITICAL*se, mean+T_CRITICAL*se],
                               school_signs=lower._signs(points[:, j]), unit='captures per individual per nominal36T')
    return dict(status='complete_additional_programme_family', confidence=CONFIDENCE,
                t_critical=T_CRITICAL, endpoints=summaries, independent_school_clusters=16,
                case_count=384, programme_criterion_met=all(x['student_t_98_75_ci'][0] > 0 for x in summaries.values()),
                school_vector_columns=list(COLUMNS),
                school_points=[dict(school_seed=school, **dict(zip(COLUMNS, points[i].tolist())))
                               for i, school in enumerate(lower.SCHOOL_SEEDS)],
                report_alongside='Always retain original H1/G36 primary97.5% and H2/G12 secondary95% estimates and decisions',
                qualification='Additional Bonferroni approximate95% four-endpoint family under individual t-interval assumptions; same16 clusters, not32',
                setting_contrast='H and bird count both change; neither factor is isolated and no optimum is established',
                bootstrap=None, native_steps=0)


def require_final_audits():
    if LOWER_FINAL_AUDITOR_SHA256 is None:
        raise ExecutionClosed('Programme production analysis closed: future lower-count independent FINAL auditor is not yet source-bound')
    # This post-analysis receipt is not part of either execution source freeze;
    # binding final audits must never require modifying a frozen protocol.
    bindings = read(HERE/'PROGRAMME_FINAL_AUDIT_BINDINGS.json')
    if not isinstance(bindings, dict) or set(bindings) != {'primary', 'lower'}:
        raise ExecutionClosed('Both independent complete FINAL receipts must be explicitly bound')
    receipts = {}
    for study, binding in bindings.items():
        if sha(binding['path']) != binding['sha256']:
            raise ExecutionClosed('Independent programme review binding changed')
        receipts[study] = read(binding['path'])
    validate_parent_final_review(receipts['primary'])
    expected = sha(HERE/'frozen_sources.json')
    review = receipts['lower']
    if (review.get('status') != 'passed' or review.get('stage') != 'final'
            or review.get('new_full_cases') != 192 or review.get('independent_schools') != 16
            or review.get('reused_discovery_cases_in_estimate') != 0
            or review.get('freeze_sha256') != expected
            or review.get('bindings', {}).get('execution_freeze_sha256') != expected
            or review.get('audit_source_sha256') != LOWER_FINAL_AUDITOR_SHA256
            or review.get('native_constructions_by_review') != 0 or review.get('native_steps_by_review') != 0):
        raise ExecutionClosed('Future exact lower-count independent FINAL acceptance required')
    return receipts


def _audited_rows(bulk, receipt):
    output = bulk/'analysis_final'
    audit = output/'analysis_audit.json'
    if sha(audit) != receipt.get('analysis_audit_sha256'):
        raise ExecutionClosed('Independent FINAL receipt must bind its exact owner analysis audit')
    table = output/'case_outcomes.csv'
    if sha(table) != read(audit)['files']['case_outcomes.csv']:
        raise ExecutionClosed('Programme raw case table differs from independently accepted analysis')
    with table.open(newline='') as handle:
        return list(csv.DictReader(handle))


def analyse(primary_rows=None, lower_rows=None):
    receipts = require_final_audits()
    primary = _audited_rows(PARENT_BULK, receipts['primary'])
    followup = _audited_rows(BULK, receipts['lower'])
    if primary_rows is not None and _parent_module()._normalise(primary_rows) != _parent_module()._normalise(primary):
        raise ValueError('Provided primary rows differ from independent FINAL accepted table')
    if lower_rows is not None and lower._normalise(lower_rows) != lower._normalise(followup):
        raise ValueError('Provided lower rows differ from independent FINAL accepted table')
    return _calculate(primary, followup)
