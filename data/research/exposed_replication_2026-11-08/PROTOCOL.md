# Frozen exposed-prey policy: fresh-school replication

The user requested continuation of the exposed-prey preference after its two
development schools produced paired differences of 0 and +7 dolphin captures.
Those exploratory results selected the policy and remain separate from this
new dataset. No policy parameter is fitted to the replication outcomes.

## Fixed scope

- New starting schools: 39063501 and 39063502, selected before feeding outcomes.
- Two random settings per school: capture-seed labels 61001 and 61002.
- Twelve dolphins alone (D), or the identical dolphins with three gannets (DG).
- Exposed-prey targeting only; eight new 36T encounters at dt=0.00125.
- All four dolphin-only encounters finish before any mixed encounter begins.
- At most four workers, one numeric thread each. No replacement schools,
  adaptive stopping, parameter sweep or additional capture seeds.

There are two independent new school realizations, each repeated under two
random settings. The four paired differences are not four independent schools.
The capture-seed label determines capture and contact-tie streams and the private
gannet target-choice streams; it is not a capture-probability-only sensitivity.

## Model freeze

controllers.py and gannet.py are byte-identical to the selected simple-cycle
pilot. The builder checks these hashes. Dolphin rules are identical in D and DG.
The controller herds for 2T of continuous proximity to any observed fish within
4.5 units, makes one feasible strike, handles/recovers, then herds again. Losing
nearby prey resets the clock; loss of a tracked dense patch does not itself
disable attacks. Target ranking prefers fewer neighbours within radius 2, then
interception effort/distance. Dense fish remain eligible.

All predator motion, point-body mouth contacts, local fish threat responses,
actual prey removal and p=0.7 conditional eligible-contact success remain fixed.
No dense-school confusion penalty, post-dive success bonus, gannet-event input
to dolphins or required coordinated dive schedule is introduced. See
ASSUMPTIONS.md for the full behavioural interpretation and limitations.

## Fresh preparation and matching

Use the original initial-state sampler and baseline scenario, with no predators.
At dt=0.00125 save each encounter checkpoint after 20T, then continue the separate
predator-free preparation through 56T for the original 36T stability screen.
Retain raw constructions, all compact preparation samples, both dispositions
and source/native/checkpoint hashes. Both candidates must pass the frozen
finite/submerged/count, route-speed and school-connectivity criteria before
feeding. No later feeding outcomes influence preparation acceptance.

The two fresh checkpoints both passed. These are seed-specific draws from the
same initialization and preparation distribution, not new environmental regimes.
Within each school/random-setting pair, fish state, dolphin physical starts,
readiness, controller state and capture/tie streams match exactly between D and
DG. Across random settings physical starts are shared and stochastic streams
differ by design. The gannet planner uses the same seeded selection algorithm.

## Verification and outcomes

Before full feeding: source-copy checks, zero-step construction/matching checks,
focused pure tests and four 4T integration cases spanning both random settings.
Full cases use fresh directories and completion seals after physical accounting,
source and private-stream replay checks. Analysis executes no native steps.

Primary outcome: dolphin captures over the full elapsed 36T, including all
herding, travelling, attack, handling and recovery time. Report each paired
difference by school and random setting, then each school's mean difference.
Report launches, contacts, qualifying proximity time, gannet captures, fish
survival and school structure. Keep prior development outcomes separate.

Do not treat capture-seed repetitions as independent school replicates. With two
new schools this is a bounded robustness check, not statistical confirmation,
biological calibration, numerical convergence or proof of long-term cooperation.
