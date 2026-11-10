# Higher-count access diagnostics

This is a descriptive reanalysis of the completed through-36 discovery map,
covering all128 bird-bearing cases on the same four previously examined schools.
It adds no simulation steps, new schools, controller decisions or bootstrap draws.
The original48-case departure outputs are preserved and explicitly reconciled.

The script verifies sealed configuration, event, trajectory and summary inputs,
then applies the existing deterministic new-target geometry to saved0.1T frames.
It reports available prey depth, geometric access, launch/contact opportunities,
and terminal whole-flock search without eligible prey. Matched differences
compare mixed groups with the same-count bird-only controls in the same school.

These are exploratory observations, not a causal test of herding, scattering,
competition or permanent bird departure. Surviving-prey depth summaries also
change when prey are removed. This analysis does not select or modify any settings
in the independent sixteen-school validation study.

Run from the research repository with its NumPy environment:

    .venv/bin/python -B research/higher_count_accessibility_2026-11-10/analyze.py

Outputs are versioned separately under this directory's outputs folder.
