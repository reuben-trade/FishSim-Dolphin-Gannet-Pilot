Private balanced high-count extension, frozen before new outcomes.

This retains all 60 completed discovery encounters and runs 48 additional
encounters at bird counts 9, 12 and 18, with all three H values and matched
bird-only controls on the same four school states. There are four independent
school units. Existing D-only controls are reused. The new high counts share
three original launch sites; point bodies can co-locate and do not avoid birds.

From the FishSim-RL root, native-free checks are:

    .venv/bin/python -B -m pytest -q research/high_count_regime_extension_2026-11-09/test_extension.py -p no:cacheprovider
    .venv/bin/python -B research/high_count_regime_extension_2026-11-09/preflight.py
    .venv/bin/python -B research/high_count_regime_extension_2026-11-09/freeze.py --stage inputs

An independent reviewer must record fresh initialization approval before the
48 actual zero-step starts. That check forbids every model-step entrypoint and
requires exact archived native fish arrays, including normalized headings.
After it passes, create the execution freeze with freeze.py --stage execution.
Fresh independent smoke approval is then required for the five fixed 4T cases.
Use supervise.py --stage smoke; bulk outputs go under /tmp. After their physical
audit and measured G18 throughput pass, fresh full approval enables
supervise.py --stage full. Full execution is bounded at 48 cases and 1,382,400
steps; the five smokes add at most 16,000 steps. No automatic retries.

The complete 108-outcome analysis contains the 60 retained outcomes and 48 new
outcomes, with 18 mixed-condition cells. It keeps per-animal contrasts against
same-H D-only and same-count G-only controls, resampling four whole-school
vectors. It is exploratory and does not establish numerical convergence,
independent validation or a global optimum. The previous held-out H1/G6
selection is unchanged and its feeding execution remains on hold.
