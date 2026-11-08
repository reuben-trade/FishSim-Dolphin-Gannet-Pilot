# Assumptions in the exposed-target replication

This study asks whether adding gannets changes dolphin feeding when the dolphins use the **same herd–strike–recover rule in both conditions**. Each encounter starts with 160 fish and 12 dolphins; the mixed condition adds 3 gannets. Counts describe this experiment, not a fitted natural aggregation. All distances and times below are uncalibrated model units; “2T” does not mean two seconds.

The behaviours below are implemented code rules. Their biological accuracy is a separate question: tests can verify that a rule executes correctly without establishing that real animals follow it.

**Dolphin behaviour**

| Implemented rule | Assumption and practical implication |
|---|---|
| Herd, make one strike, complete handling/recovery, then herd again. | A prescribed feeding cycle, with no learned strategy or adaptation across encounters. |
| Accumulate 2T continuously while at least one currently observed fish is strictly within distance 4.5. Losing that proximity resets the clock. | Nearby fish are a proxy for contributing pressure while herding movement is requested. This does **not** verify successful compaction, completion of a bait ball, complementary pod coverage or sustained pressure on the same fish. |
| A tracked local fish patch supplies an ahead/side/below movement waypoint using the inherited geometry. | Each dolphin acts from its own observation. There are no assigned pod roles, synchronized releases, target reservations or explicit messages between dolphins. Herding contributions can overlap. |
| Patch handoffs and fragmentation do not reset a continuous proximity clock. Without a usable patch, the dolphin searches; nearby isolated fish still count toward the clock and remain strike candidates. | A dense cluster is not required for feeding. This allows dolphins to exploit scattered prey rather than making fragmentation prevent attacks. |
| After 2T, select among all currently physically feasible fish. If none is feasible, continue herding and retain readiness while proximity continues. | There is no fixed maximum waiting window or compulsory attack against unreachable prey. |
| Prefer the feasible fish with the fewest observed neighbours within radius 2; break ties by predicted interception-plus-turning time, then distance, then fish identity. | “Exposed” is a **soft preference**, not an isolation threshold. Dense fish remain eligible. This ranking is a hypothesis about target choice, not a fit to field observations. |
| See exact positions, velocities and persistent identities of living underwater fish within radius 25. | Perception has no noise, occlusion or directional blind sector. Identity persistence and constant-velocity interception are idealizations. |
| Launch only within distance 6, with a feasible intercept inside horizon 3 and predicted turn-plus-intercept time inside a maximum 6T bout. Keep the selected target during the committed attack. | Motion and reachability constrain opportunities. There is no retargeting inside an attack; target loss or timeout can end it. Another fish intersecting the mouth path can nevertheless be caught. |
| After success, remain stationary for 2T; after failure, remain stationary for 0.75T. The next strike requires a fresh pressure cycle. | These fixed recovery durations are engineering choices, not measured dolphin handling or physiological recovery times. |

**Gannet behaviour**

| Implemented rule | Assumption and practical implication |
|---|---|
| Observe the current fish distribution across the modelled domain, restricted to underwater fish within detection depth 12. | Gannets have idealized global information, without angular restriction, occlusion or observation noise. Detection and physical dive accessibility remain different constraints. |
| Form density clusters with DBSCAN radius 2 and minimum sample count 4, including the focal point. | These thresholds define model patches; they are not measured gannet perceptual categories. A prescribed number of clusters is unnecessary. |
| Choose an eligible cluster with probability proportional to its number of physically accessible fish, using each bird’s private random stream. | Large accessible clusters attract more selections. This is a target-selection probability, not a capture-success probability or an empirically fitted preference. |
| Aim at the accessible fish with the most neighbours within radius 2; resolve ties by distance and identity. If no eligible dense cluster exists, use the densest accessible local neighbourhood. | Birds remain able to attack sparse prey. A target’s density does not guarantee an actual contact. |
| Retain inherited flight, plunge, underwater pursuit, ascent, depth/travel limits and recovery mechanics. | Gannets do not wait for a dolphin “herd ready” signal and do not intentionally create dolphin feeding opportunities. Birds may dive before the dolphins complete a pressure cycle. |

**Fish, capture and shared limitations**

- Fish move at constant model speed 3 with deterministic schooling and local threat-response steering; native movement noise is zero. Nearby underwater predators alter escape/social steering. There is no gannet-specific “panic” flag or response to airborne predators. Scattering must arise from the ordinary dynamics and is not guaranteed by a dive.
- There is no dense-school confusion penalty, post-dive capture bonus or automatic reward for cooperation. Density and scattering can affect trajectories, target choice and opportunities to make contact.
- Dolphins and gannets both use **0.7 success conditional on an available eligible oral contact**. This is not 70% success per strike or dive. A strike can fail before reaching any fish. The first such contact closes the bout after its success/failure draw; each bout can consume at most one fish.
- Capture uses the shared swept mouth geometry: an offset mouth sphere, radius 0.4 and forward offset 0.3, meeting a point-represented fish in the forward body hemisphere underwater. This is a simplified feeding geometry, not a detailed jaw/body collision model. Predator body-spacing avoidance is disabled.
- Captured fish are removed uniquely. The finite school is not replenished, so depletion and competition can change later opportunities. There is no food sharing or passive consumption by a dolphin that has not entered an attack.
- There is no learning, fatigue, hunger, satiety, explicit energy budget or calibrated energetic cost. All predators use fixed capabilities. Capture counts and encounter time therefore cannot directly establish energetic profitability, fitness or real-world feeding rates.
- Movement/contact coupling uses the existing timestep of 0.00125T. The pilot is not a new timestep-convergence or biological-calibration study.

**How to interpret this replication**

Cooperative herding within the dolphin pod and a benefit from adding gannets are separate questions. The paired comparison measures the effect of gannet presence on these dolphins under fixed model rules. A positive difference would support facilitation in this model. It would not establish intentional interspecies collaboration. Gannet captures in mixed encounters also cannot establish a reciprocal benefit to birds without a matched gannet-only comparison.

The earlier roughly 17% increase on the development cases motivated selecting the exposed policy. It is preliminary evidence used for selection, not independent confirmation. The continuation uses **two fresh schools crossed with two capture-seed settings and two presence conditions: eight encounters**. It provides four matched presence comparisons, but only two independently generated new school configurations—not four independent schools. Results should show each school and seed combination rather than treating the eight encounters as independent ecological replicates. The random-stream setting also determines the private gannet target-selection stream in the current builder.

The most sensitive assumptions to keep visible are the proximity-based herding proxy, the exposed-target preference together with an uncalibrated constant contact-success rule, and idealized predator perception. This replication holds them fixed to test repeatability of the observed effect; it does not validate those assumptions.

Implementation references: [dolphin controller](controllers.py), [gannet targeting](gannet.py), [encounter construction](build.py), [shared movement and observation](../prey_mediated/predators.py), [shared contact mechanics](../prey_mediated/contacts.py), and [fish–predator coupling](../prey_mediated/encounter.py).
