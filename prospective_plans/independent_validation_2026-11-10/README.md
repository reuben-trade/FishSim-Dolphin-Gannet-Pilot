# Frozen validation configuration archive

This compact archive identifies the design fixed before the16:44:36 Perth feeding launch on10November2026. It is publicly posted later, after some single-species control encounters had completed. It is not formal preregistration and makes no claim of public posting before data collection. `POSTING_RECORD.json` records the first successful public-push confirmation time and commit after publication.

The protocol, analysis plan, case-identity source, execution freeze, root design authority and pre-feeding review/approval records are byte-exact copies. Their original author paths and stage-specific permissions remain as provenance. The2,127-file execution-freeze manifest is included; its underlying full scientific source/raw/checkpoint bundle is not duplicated here. This configuration archive is not a runnable simulation package and contains no full36T feeding outcomes or synthetic layout data.

`case_inventory.csv` is the planned192-case inventory, generated only from the archived `cases.py` using standard-library code. It has16 schools,32 school×randomness-label worlds, two grids and three matched arms. It contains no captures, contacts or realised launches. Verify it without any model import, data loading or stepping:

```bash
python -B prospective_plans/independent_validation_2026-11-10/generate_case_inventory.py --check
```

To regenerate elsewhere, supply `--output /path/to/new.csv`; existing files are not overwritten. `GATE_RECEIPT_HASHES.json` identifies the source, actual-start and engineering records. The full192 actual-start record is identified by hash rather than duplicating its arrays/receipts in this compact release. Six4T engineering checks are not36T feeding evidence. Earlier permission flags describe their original stage; the later feeding approval binds the full execution.

Read the [public plan](../../reports/supplements/VALIDATION_PREANALYSIS_PLAN.md). The current paper and main notebook still describe the separate discovery results; no validation effect is claimed here.
