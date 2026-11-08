# Local gannet timing: bounded feasibility check

This is an engineering check of an imposed one-way launch deferral. It is not a biological oscillator, a full feeding comparison, or a test of prey-region arrival synchrony.

## Fixed design

The predeclared first fresh school (39063501) and random setting (61001) were reused. The exposed dolphin cycle, global dense gannet targeting, physical motion, recovery, oral contact and conditional capture probability were unchanged. Only a physically legal gannet orient-to-plunge transition could be delayed. The gate needed a previously committed dolphin launch, published after its physical step, no older than 2T, within 12 spatial units of the gannet and with its prey region within 4 units of the current gannet target. A qualifying cue would request release one model-time unit after the dolphin launch. The gannet would continue ordinary flight and turning while waiting; no extra attempt was created.

The authorized native allocation was 4T with the wrapper disabled, followed by 8T with lag1 enabled: 9,600 native steps, 12T total. Already sealed baseline outputs supplied the equal-horizon 4T reference and the fixed first8T reference; neither reference was rerun. No post-outcome parameter adjustment was made.

## Results

The disabled4T run reproduced every retained trajectory, initial/final fish and predator state, actual event and private capture/target/tie random stream exactly.

In the enabled8T run, 15 actual committed dolphin launches were published. All six original legal gannet launch decisions lacked a qualifying local cue, so no plunge was deferred. There were six gannet launches and three water entries within the horizon. The completed encounter produced five dolphin and one gannet captures, exactly the same as the fixed first8T baseline prefix. All 81 retained frames matched that prefix exactly.

The completed outputs passed their original seals/audits and an independent read-only review of committed cue provenance, original horizontal plunge eligibility, resolved oral geometry, capture and target random streams, recovery readiness and unique fish removal. The review executed no native steps.

## Interpretation and stopping decision

The isolated wrapper can replay the original model correctly, but this native feasibility run did not exercise its delay. Identical outcomes therefore provide no evidence for or against a benefit of attack timing. The predeclared requirement of at least one actual legal deferral was not met. No full timing experiment, lag adjustment, longer encounter or wider cue threshold was launched. Objective3 remains open.

A subsequent timing study would first need an explicitly revised opportunity/cue design and a declared delay control to distinguish temporal alignment from reduced realised effort. A launch lag alone must not be described as a water-entry or prey-region arrival lag.

## Evidence

- `protocol.json`, `timing.py`, `run.py` and `test_timing.py`: frozen intervention and bounded execution path.
- `results/disabled_4T_v1/exact_baseline_parity.json`: exact disabled comparison.
- `results/lag1_8T_v1/feasibility_review.json`: enabled audit, outcome counts and stopping criterion.
- `results/*/cases/*/completion.json`: per-file completion seals and source manifests.
- `review_feasibility.py`: independent read-only review; not part of the scientific intervention.

Space and T are uncalibrated model units. The two horizons are integration checks and do not substitute for the36T feeding studies.

## Read-only check of later baseline opportunities

A subsequent retrospective screening used all four sealed36T fresh DG baselines, covering73 actual gannet launches and232 dolphin launches. It executed zero native steps and changed no scientific parameters. Exact event times and target IDs were combined with saved positions. Predator event positions were bounded by the intersection of speed balls from their two bracketing saved endpoints; fish event positions used the nearest living snapshot and a speed bound, plus a conservative within-step prediction allowance. This identifies qualifications only when the entire uncertainty interval lies inside the original12/4 distance limits. Cue age had to exceed2dt to guarantee publication in an earlier step.

One later baseline launch met those conservative requirements: school39063501, random setting61002, G0bout6 at elapsed25.5637578266T. The preceding D10bout4 launch was0.7968527655T earlier. The body-distance interval was[11.42045,11.44945], below12; the target-region interval was[2.05939,2.50542], below4. A requested1T release was therefore still0.2031472345T in the future. The other three baselines had no possible qualified actual-launch pair under the motion bounds. In particular, the original enabled8T case (setting61001) had none through36T.

This shows that the8T feasibility horizon misses at least one available later opportunity in a different random setting. It does not demonstrate an actual deferred plunge or feeding effect: the calculation screens the unchanged baseline, and the altered trajectory after any intervention remains untested. Any enabled follow-up selected using this screening must be labelled post-hoc engineering validation, not fresh confirmation.

Evidence: `results/retrospective_36T/screening.json` and `candidate_launch_pairs.csv`; reproducible read-only source: `retrospective_opportunities.py`.


## Single later engineering demonstration

Before new native execution, root approved one36T enabled run using school39063501/random setting61002, selected solely from the retrospective opportunity screening. `demonstration_protocol.json` records this amendment and its additional28,800-step budget. The original8T protocol, source and outputs were retained. No cue threshold, lag, behavioral parameter or checkpoint was changed. This is an opportunity-selected post-hoc engineering demonstration, not independent confirmation or an estimate of the best lag.

The hook exercised one held bout, G0bout6, at25.5637578266T. It continued ordinary flight while waiting, then cancelled the wait at25.6400000000T because the gannet left the cue's12-unit locality. The resulting hold lasted0.0762421734T. Actual launch occurred0.8730949389T after the dolphin cue, before the requested1T release. Consequently there was **one partial hold and zero successful requested1T releases**. The121 waiting-gate evaluations belong to that single hold; they are not121 independent attempts. Surface-entry timing is recorded separately and is not prey-region arrival.

Both species had the same catches and launch counts as the36T ordinary baseline: dolphins24catches/60launches and gannets11catches/20launches. Resolved oral contacts changed from34to35 for dolphins and12to13 for gannets. Equal catches in this single selected encounter give no evidence of a feeding gain from the imposed timing policy.

The original physical/source/random-stream audit and independent oral geometry, cue provenance, original launch eligibility, recovery and unique-removal reviews passed. All256 saved frames before intervention were bitwise identical to the baseline. The prior complete-step event prefix also matched exactly:599 general events,128 cycle events and182 bird-analysis events. A target-selection diagnostic stamped at the intervention step's beginning contains the committed end-of-step mode, so that one context record correctly differs at the intervention boundary; its selected target and probabilities were unchanged.

Receipts: `results/lag1_36T_demonstration_v1/demonstration_validation.json`, `demonstration_review.json` and `event_prefix_and_effort_review.json`. The engineering budget is complete:38,400 native steps across the original12T feasibility allocation and this additional36T demonstration. No further lag search or timing experiment was started.
