# Simple herd–strike cycle: paired gannet pilot

This isolated quick pilot replaces the adaptive dolphin release rules with one
short, repeatable individual cycle. It compares dolphin feeding with and without
gannets while keeping each dolphin policy identical across the presence pair.
Earlier studies and their results remain unchanged.

## Frozen comparison

- Two existing development schools: 39061001 and 39061002; 160 initial fish.
- Two dolphin policies: `nearest` and `exposed`.
- Twelve dolphins alone (D), then the same dolphins with three gannets (DG).
- Eight full encounters: two schools × two policies × two presence conditions.
- Each encounter lasts 36 model-time units (T), dt=0.00125, capture seed 61001.
- Complete all four D encounters before starting the four DG encounters.
- Use at most four workers, with one numeric thread per worker. No parameter
  sweep, extra capture stream or additional school is included automatically.

Initial fish, dolphin states/readiness, capabilities and private capture streams
are matched across each pair. Both policies use the same cycle and physical
attack checks; only eligible prey ranking differs. Paths and subsequent random
draw counts may diverge as the encounters evolve.

## Dolphin cycle

Each dolphin moves using the existing local herding/pressure waypoints. It earns
an attack opportunity after **2T of continuous actual proximity pressure**: at
least one currently observed fish must remain strictly within the existing fish
threat radius, 4.5 model units. Time spent merely travelling towards the herd does
not count. Loss of nearby prey resets the clock. Tracking a different patch or
school fragmentation does not reset it if nearby prey remain.

Once ready, the dolphin launches one attack when any observed fish passes the
shared physical interception, turning and launch-range checks. It then completes
the unchanged attack, handling or miss recovery, and begins a fresh herding
cycle. No whole-school compactness threshold, expansion threshold, outward-speed
threshold, gannet-event trigger or synchronized pod-wide release is used.
Nearby dolphins can strike independently while others keep herding; no permanent
nonfeeding guards or fixed number of simultaneous attackers is imposed.

- `nearest`: rank all physically eligible fish by distance, then stable fish ID.
- `exposed`: rank all physically eligible fish first by the number of neighbours
  within radius 2, then interception/turn effort, distance and stable ID. This is
  a preference for less crowded prey, not an exclusion of dense-school prey.

An isolated reachable fish remains eligible even without a tracked dense patch.
No eligible fish means continued herding/search rather than a fabricated strike.
The 2T clock and target ranking are explicit engineering assumptions, not fitted
dolphin decision rules.

## Gannets and physical mechanics

Copy `gannet.py` exactly from the completed paired C pilot. Preserve its source
hash, global current underwater observation within detection depth 12, DBSCAN
radius 2/minimum count 4, accessible-count-weighted cluster selection and densest
accessible target. Retain the same independently seeded targeting streams for
each school/capture-seed/bird combination. Dense-cluster absence falls back to
the densest accessible neighbourhood; no accessible fish means continued search.
Birds receive no herd-ready signal and no imposed dive schedule.

Keep all inherited predator speeds, turns, target commitment during active bouts,
dive limits, handling/recovery, point-body swept oral geometry, fish response and
actual unique prey removal. Both species retain **0.7 success conditional on an
eligible mouth contact**, not per attack or dive. There is no dense-school
confusion penalty or post-dive success bonus. This run does not calibrate feeding
probabilities or guarantee that adding gannets helps dolphins.

## Execution and reporting

Run focused controller, gannet and integration checks before the full cases.
Use the accepted native binary and exact helper acceleration. Save source hashes,
initial/final states, exact attack/contact events, per-dolphin cycle diagnostics,
bird target decisions, sampled trajectories and completion seals in fresh run
directories. Do not overwrite or retune completed cases after inspecting food.

Report each school's D-versus-DG difference separately for each policy, then
pooled descriptive totals. Primary outcomes are dolphin captures over the full
36T and captures per initial dolphin per total elapsed time, including herding
and recovery. Also report attacks, contacts, gannet captures, achieved pressure
cycles, fish survival and school structure. A negative or mixed result is a valid
outcome. Two development schools and one capture stream do not establish
biological calibration, statistical generality or long-term mutual cooperation.
