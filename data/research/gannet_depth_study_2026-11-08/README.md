# Gannet initial depth and matching single-species controls

This isolated pilot retains the frozen gannet, fish, movement and point-mouth contact model used in `exposed_replication_2026-11-08`. No dolphin enters the encounter, and no dolphin controller is instantiated or executed. Gannets have the same global prey sensing within detection depth12, private density-cluster selection RNG, capabilities, readiness, conditional contact probability0.7, and capture/tie RNG as the corresponding completed mixed encounter.

The fixed design is recorded in `protocol.json`, and `frozen_sources.json` records all selected scientific sources before any pilot model steps. The eight full encounters last36T each: schools39063501 and39063502 at unchanged depth, mean8 and mean11 with capture seed61001, plus both unchanged-depth schools with seed61002. Four unchanged-depth G-only cases supply controls for the four completed DG repetitions. These four repetitions represent two independent school configurations.

Only fish z coordinates are translated. Shape, density, headings, stable IDs, XY coordinates and clocks remain unchanged. Gannets remain at z3; fish habitat preference remains depth5 with deadband±2. The targeting depth reference is7.93028 model units, distinct from detection depth12 and maximum bird body depth12. Accessibility is a coarse travel/depth condition, not guaranteed interception.

The earlier depth handoff described an older fixed-versus-pursuit programme and finite-body geometry. Latest user authorization retained the completed simple exposed dolphin model and original point representation. This study uses that same accepted shared gannet/fish/contact baseline; no older variant is substituted. Model lengths and T are uncalibrated, and numerical convergence remains unestablished.

## Execution

From the repository root:

```sh
.venv/bin/python -m pytest research/gannet_depth_study_2026-11-08/test_depth.py -q
.venv/bin/python research/gannet_depth_study_2026-11-08/run.py --controls --output research/gannet_depth_study_2026-11-08/results/controls_v1 --workers 3
.venv/bin/python research/gannet_depth_study_2026-11-08/analyze.py --controls --output research/gannet_depth_study_2026-11-08/results/controls_v1
.venv/bin/python research/gannet_depth_study_2026-11-08/run.py --smoke --output research/gannet_depth_study_2026-11-08/results/smoke_v1 --workers 2
.venv/bin/python research/gannet_depth_study_2026-11-08/run.py --execute --output research/gannet_depth_study_2026-11-08/results/full_36T_v1 --workers 3
.venv/bin/python research/gannet_depth_study_2026-11-08/analyze.py --output research/gannet_depth_study_2026-11-08/results/full_36T_v1
```

Output directories must be new; these commands document the executed paths and must not overwrite them. Reproductions use fresh output paths. Each case records matching initial states, actual contacts/entries, sampled trajectories and depth/accessibility, replayed private streams, unique prey removals, source hashes and completion seals. The eight full cases use230400 native steps; all declared controls and smokes bring the fixed budget to249600 steps/312T. At most four workers may run, coordinated with other jobs.

## Staged findings before full encounters

Fifteen zero-step tests passed, including exact G projection against every corresponding mixed initial state. Four4T predator-free controls passed without surface reflections. Mean8 relaxed to7.011/6.994 and reference accessibility rose from44.375/45% to86.25/88.125%. Mean11 relaxed to8.462/8.362 and accessibility rose from0 to31.25/33.125%.

This is therefore an **initial-depth transient comparison**, not a maintained-depth feeding curve. No habitat setpoint was moved to conceal that limitation. Both4T G smokes passed; each launched three attacks and captured one fish. The deep smoke first selected an accessible target at0.839T, after native prey motion created one. Selection depths, actual mouth geometry and private capture draws were checked.

The depth effect may concern initial opportunity delay and exposure history. A full-encounter feeding difference cannot establish that dolphins are required to raise deep fish. Matching G-only versus DG baselines can test modelled reciprocal benefit, but do not establish conscious cooperation. No controlled interspecific timing experiment runs in this study.
