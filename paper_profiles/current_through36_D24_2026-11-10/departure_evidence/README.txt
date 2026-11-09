SAVED DEPARTURE EVIDENCE — 9 November 2026 surface-access revision

The original twelve source files are exact copies of previously completed
diagnostic exports and figures. V3 adds the exact existing cessation_summary.json
as a thirteenth input, so resumed launch gaps can be reconstructed from the
recorded clocks. No analysis, plot, simulator or bootstrap was rerun.
provenance.json records original paths, byte sizes and SHA-256 hashes.

FOUR RUNS WITH NO NEW GANNET LAUNCH IN THE FINAL6T
School    Treatment                  Last launch(T)  State at36T
39061001  H1 /6 gannets /mixed       17.668          Whole flock searching; shallow fish beyond travel gate
39061002  6 gannets only             14.128          Whole flock searching; shallow fish beyond travel gate
39061001  1 gannet only              29.064          Orienting; targets available
39061002  H3 /3 gannets /mixed       29.714          Orienting/ascent; a target available

Human times are rounded to0.001T after removing accumulated clock roundoff
below0.00000001T. The companion CSV preserves each full source clock string.
T is uncalibrated model time, not seconds. Last launch is not attack ending.

The bank has36 mixed and12 gannet-only bird-bearing encounters reusing four
previously examined schools. Whole-flock terminal loss occurs in1/36 mixed
and1/12 bird-only runs. A further20/48 bird-bearing runs resume launches after
a gap of at least6T. The other two terminal pauses still have target access.
These are setting-level counts, not48 independent schools or wild prevalence.

ACCESSIBILITY AND REACQUISITION
The operative new-target depth cap reserves room for turning and ascent:
12 -6/(pi/2) -.25 =7.9302813658 model units. Configured detection/max depth12
is therefore not the entire access rule. A target must also pass the travel
budget: (horizontal distance + positive air height)/10 +depth/6 <=6T.
Both whole-flock losses begin with a sampled depth blackout. Birds then fly
straight while searching. By36T, shallow fish have returned, but birds have
travelled too far away to pass that gate. One case has no dolphins. These
records motivate separate surface-herding and bird holding/reacquisition
tests; they do not establish that the retained dolphin rule actively keeps
prey at the surface or that intentional collaboration is necessary.

DEFAULT TIMECOURSE IS A SINGLE SCHOOL, NOT THE FOUR-SCHOOL MEAN
Default=s39061001_H1_G6_DG_c61001. Dolphins end at27 fish versus23 in their
matched dolphin-only control (+17.4%), after briefly reaching0% around20–21T.
Gannets end at2 versus7 in the same-count bird-only control (-71.4%); they
already trail before launches stop. This is distinct from pooled H1/G6 dolphin
catches113 versus91 across four schools.

The final committed attack ends at19.56375T (about19.564T). Fully observed6T
windows around that ending give dolphin catches5vs4 before and9vs7 after.
Only this mixed run has complete6T windows on both sides of the final attack
end:24/36 are still attacking at the horizon and11 end too late. Neither a
persistent benefit collapse nor a general no-effect conclusion is supported.
Zero captures in both bird treatments give undefined percentage gain, not
improved feeding. Ascent and prey responses can continue after attack ending.

FILES
ASSESSMENT.txt: complete prior interpretation, definitions and limitations.
cessation_summary.csv: all48 bird-bearing cases and endpoint/gap classifications.
bird_details.csv: saved per-bird outcomes, not independent biological samples.
sampled_accessibility.csv: sampled live-school state and eligibility.
benefit_by_time.csv: all36 mixed/control cumulative and trailing-window contrasts.
before_after.csv: exact before/after windows with missing/censoring reasons.
benefit_summary.json: availability counts by anchor/species.
benefit_audit.json: prior passed prefix-accounting audit, zero native runs added.
benefit_default.pdf: default trajectory contrasts.
benefit_atlas.pdf: all36 mixed-run benefit plots.
cessation_overview.pdf: all48 bird-bearing attack timelines.
departure_depth_accessibility.pdf: the two whole-flock losses.
four_final_6T_no_launch_runs.csv: compact derived human table; raw clocks retained.
