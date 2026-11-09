# Private v6 model example candidate (v4 front end)

The professor-facing entrypoint is `run_v6_example.py`. Its default is a native-free plan, using the separately source-built cc21 artifact already protected in the published package. `--check` explicitly requests strict actual initialization with zero steps. `--quick` explicitly requests a bounded D/DG pair, automatically performing or reusing the immutable 108-start check. No user-authored approval JSON is needed. `--native-kind historical` selects the original EB artifact instead. Native execution requires Linux x86-64 CPython 3.12; this new interface has not yet been natively validated.

```bash
python -B run_v6_example.py --plan --package-root /path/to/FishSim-Dolphin-Gannet-Pilot
python -B run_v6_example.py --check --package-root /path/to/FishSim-Dolphin-Gannet-Pilot
python -B run_v6_example.py --quick --setting headline --package-root /path/to/FishSim-Dolphin-Gannet-Pilot
python -B run_v6_example.py --quick --setting joint --package-root /path/to/FishSim-Dolphin-Gannet-Pilot
```

Every execution writes a permanent `execution_request_v1` declaration beside its outputs. It records explicit local opt-in and expressly does not claim independent review or historical study authority. The request generator and all interface files are bound by the runtime/source manifest. A separately supplied static interface-source-review artifact records developer validation of the code, not user permission. That source review is absent from this preparation; no native execution is enabled until independent review is recorded.

Zero-check receipt, permanent request and source-review hashes are sealed and checked before reuse. Invalid or incomplete checks stop rather than retry. Protected, reused or unwritable explicit pair outputs are rejected before actual initialization. Both original and generated physical/accounting source fingerprints remain unchanged from frozen v3; v1/v2/v3 stay preserved.

This additive prototype uses the published v6 high-count model. The default `--setting headline` selects **H=1T/G=9 for 4T**; `--setting joint` selects **H=2T/G=12 for 2T**. Both use a matched D-only then mixed D/G pair from the first school by default. `--integration` selects 0.5T, and `--duration` permits only 0.5T, 2T or 4T. These are bounded execution examples, not feeding-benefit estimates. There is no 36T or full-ensemble execution option.

The runtime verifies v6's complete 2,100-entry source/dispatch closure and the protected model source. All original scientific files, archived approvals, checkpoint arrays, builders and runners remain byte-identical. Five JSON declarations receive explicit derived path/native compatibility bindings. Original preparation and native-reference provenance remains recorded separately; archived approval files never authorize a new execution.

The generated `regime_example_build.py` replaces only two historical artifact-gate statements. Its pure preparation, actor roster/readiness/private-stream formulas and physical constructor body retain exact AST. The separately named execution harness replaces only the historical operational/horizon gates; every motion, contact, private-stream replay, prey-removal and accounting statement retains exact AST. Original/adapted fingerprints are stored in the runtime declaration.

Preparation covers **all 108 matched starts on the same four schools**: 60 retained starts with G=0/1/3/6 and 48 new starts with G=9/12/18. It does not add independent samples. Golden actual starts select the correct retained-v2 or high-count case folder, whose arrays/receipts are protected by the v6 manifest.

Native-free preparation commands:

```bash
python -B run_regime_model.py --plan --package-root /path/to/FishSim-Dolphin-Gannet-Pilot
python -B run_regime_model.py --plan --setting joint --package-root /path/to/FishSim-Dolphin-Gannet-Pilot
python -B run_regime_model.py --prepare --package-root /path/to/FishSim-Dolphin-Gannet-Pilot --runtime /tmp/my_v6_example/model
```

`--plan` verifies input hashes and imports no FishSim extension. `--prepare` copies a private runtime and checks all 108 Python states/planners/private-stream initializations, explicitly blocking extension import, native construction and stepping. A separately rebuilt module can be selected with `--candidate-native` and an exact `--candidate-record`; pure preparation neither imports nor tests that module.

The original EB artifact remains retained for the unchanged pure actor-reference pin. The selected active execution module is declared separately (historical EB or independently built cc21). No scientific sources have been rebuilt for this prototype, and no compiler/backend numerical-equivalence claim is made.

Actual `--check` is a separately reviewed 108-construction/zero-step gate. It blocks `Encounter.step`, `TravellingSchool.step` and `SurfaceSafeSchool.step`, probes the fresh output parent before construction, and requires **exact archived actual fish arrays, actors, controller and private RNG states**, including for the rebuilt module. A mismatch fails the gate; no normalization allowance is applied to actual archived arrays. The raw-checkpoint heading check separately documents the unchanged constructor's normalization bound.

Actual checking/integration accepts only an explicit local execution request from the reviewed interface. The static source review and later bounded validation receipts remain distinct from those user requests. The analysis notebook remains native-free by default.

Proposed validation is 108 zero-step starts per binary (216 total, zero integration steps), followed on each binary by H1/G9 D/DG at 4T and H2/G12 D/DG at 2T (19,200 steps). One additional cc21 frontend 0.5T pair reuses its completed zero check, adding 800 steps: **20,000 integration steps total, one worker, no extra initialization sweep**. Successful catches are not a pass criterion. This preparation does not approve or execute that plan. Native import/construction/integration, Docker/builds and publication remain unperformed by this task.
