# Watch saved simulations

Run these commands from a terminal opened in the repository root, rather than
in a notebook code cell:

```bash
python -m pip install -r requirements-analysis.txt
python tools/watch_replays.py
```

The launcher starts a local HTTP server and opens the replay browser. Leave
that terminal running while viewing; press Ctrl+C to stop. It reads bundled
trajectories and events. It does not import the native simulator, change
behaviour or generate a new run. Only selected runs need their trajectory
payloads loaded.

For an existing Python environment, the viewer needs NumPy and the Python
standard library. The analysis requirements also install JupyterLab and
Matplotlib for the notebook.

## Included runs

The selector includes all **108 completed 36T encounters** in the current
discovery map: four schools, H=1/2/3T, 1/3/6/9/12/18 gannets and the
corresponding solo controls. Each run loads from its preserved trajectories
and events; this does not add independent schools.

The lower-count bank and higher-count extension retain distinct provenance.
The viewer shows percentages only when its strict matching checks pass.
In particular, higher-count dolphins share their solo controls with the
earlier bank, so their cross-study gain can display NA here. The reviewed
full-map effects remain available in the notebook; no matching rule is
silently relaxed for the viewer.

## Controls

1. Choose a saved run from the catalog. Filter by school, herding interval,
   bird count or species presence.
2. Watch A alone, or select A and B for a shared clock and camera. Use the
   matched dolphin-only or gannet-only control for the relevant comparison.
3. Play/pause, drag the time slider, or jump between attacks and captures.
4. Select 3D, top or side view. Drag in the 3D view to rotate; use zoom and
   camera framing to inspect dives, pursuit and school disruption.
5. Read species and individual captures alongside physical attack states.
   Outcome comparisons cover the complete encounter, independently of the
   playback clock. Relative percentages are undefined when the reference is
   zero or the comparison has no matching reference.

Orange circles mark dolphins, green diamonds mark gannets and blue points
mark fish. Outlines and target lines identify attacks. Captured fish
disappear according to the saved alive mask; exact event clocks may fall
between retained visual frames. T and distance are uncalibrated model units.

## Remote machine or occupied port

```bash
python tools/watch_replays.py --no-browser --port 8765
```

Open the local address printed by the launcher. For a remote server, forward
the localhost port through your SSH session. The viewer binds to localhost;
it does not publish the data to an external service. Use `--help` for options.

## Recording in the README

The [animated recording](media/dolphins-gannets-2026-11-09.gif) and
[full WebM video](media/dolphins-gannets-2026-11-09.webm) show
`s39063501_H2_G6_DG_c61001`: 12 dolphins, 6 gannets, H=2T, 160 initial fish,
all 361 retained frames from 0–36T. Final catches are 25 for dolphins and 16
for gannets. The [provenance JSON](media/dolphins-gannets-2026-11-09.json)
records source hashes, camera settings and per-frame counters. This example
is part of the lower-count regime bank used in the current paper; it is
not a new independent encounter or evidence of an optimal policy.

For numerical results and model limitations, use [main.ipynb](../main.ipynb)
and the [scientific overview](STUDY_OVERVIEW.md).
