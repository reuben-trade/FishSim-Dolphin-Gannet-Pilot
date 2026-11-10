# Crossed herding-duration and gannet-count follow-up

Complete the two missing mixed conditions, H1/G12 and H2/G36. Together with the
primary H1/G36 and queued H2/G12 studies, this gives a 2×2 design that estimates
herding-duration and gannet-count effects separately at these two tested levels.
This design was written after primary controls began and before the first
complete paired feeding effects were inspected. No feeding outcomes were read.

| Mixed condition | Source | Matched dolphin-only control | Matched gannet-only control |
|---|---|---|---|
| H1/G12 | New follow-up | Primary H1/D-only | Queued G12-only |
| H1/G36 | Primary study | Primary H1/D-only | Primary G36-only |
| H2/G12 | Queued lower-count study | Queued H2/D-only | Queued G12-only |
| H2/G36 | New follow-up | Queued H2/D-only | Primary G36-only |

Use the same sixteen schools, two nested world labels, two timesteps and
nominal 36T encounters. The new work is 128 mixed encounters: **5,529,600 steps**.
Four separate 4T engineering encounters add **19,200 steps**, giving a total
new ceiling of **5,548,800**, with no new predator-free preparation. The
combined design references 512 unique full encounters: 384 existing/planned
encounters plus 128 new ones. Its 256 unique controls are reused by exact
source case, and the independent sample remains sixteen school clusters.

`new_mixed_cases.csv` lists the new encounters; `engineering_smokes.csv` lists
the four excluded engineering runs. `new_case_control_map.csv` supplies each
new mixed case's two exact control references. `paired_control_map.csv` lists
all eight unique outcomes for each school/label/grid combination. Empty
completion hashes and the lower study's future execution-freeze hash remain
pending complete independent audits. They are never inferred or zero-filled.

For school *i*, label *r*, grid *d*, herding duration *h* and count *g*, let
*M* denote mixed captures and *A* the matching species-only captures. Define
the partner-benefit effects, in fish per individual per nominal 36T:

```text
eD(h,g) = [MD(h,g) − AD(h)] / 12
eG(h,g) = [MG(h,g) − AG(g)] / g
E(h,g)  = mean of the two label effects within each school

Count effect at h:     E(h,36) − E(h,12)
Herding effect at g:   E(2,g) − E(1,g)
Interaction:          E(2,36) − E(2,12) − E(1,36) + E(1,12)
```

Form these contrasts within each school, preserving shared-control covariance.
Use integer world numerators `3×(MD−AD)` for dolphins and
`(36/g)×(MG−AG)` for gannets. Both have denominator 36; summing two labels gives
school denominator 72. This preserves exact zeros and control cancellations.
For each contrast, report the sixteen-school mean, sample SD, SE=SD/4 and
95% pointwise Student-t interval with df15 and critical value 2.131449545559776.
Report raw group captures and per-animal food alongside these effects; divide
by 36 only for rates, including coherent early depletion.

The fine grid is the main grid for secondary estimation. The coarse grid and
paired fine-minus-coarse differences assess numerical sensitivity. Retain the
full predeclared 18-component vector: four cell effects, two count contrasts,
two herding contrasts and one interaction for each species. These are
pointwise descriptive estimates, with no automated success criterion or new
confirmatory family. The original primary 97.5% criterion and additional
four-endpoint programme 98.75% analysis remain unchanged.

At eight workers, completed timing-only observations give a roughly **12-hour
throughput reference** for the new full schedule. A provisional **12–18-hour
planning allowance** covers variation and overhead; it is not a measured G12
forecast or guaranteed bound. Fine-mixed and clean G12 timings remain
uncalibrated. The operational snapshot records one thread per worker and about
1.3GiB for eight times the observed peak worker memory. Allocate roughly 15GiB
for new outputs and recheck at least 23GiB free at the later start, preserving
8GiB root and 2GiB temporary-space reserves. Raw controls are referenced rather
than copied.

Execution is closed. Both 192-case studies must finish and pass independent
FINAL evidence audits, irrespective of their effect signs. A separate finite
root authority, reviewed native harness, source/input/actual-start proof,
engineering and feeding approvals are then required. H and bird count vary
while twelve dolphins, prey, physical rules and original private-stream
formulas stay fixed. Bird number changes multiplicity at three fixed launch
sites. The design tests these model conditions and their interaction; it does
not establish an optimum or independently validate real animal behaviour.
