# Synthetic renderer lineage

This v2 corrects the two auxiliary CSV labels in the unactivated v1 candidate.
All six usable synthetic CSV exports now have both a `SYNTHETIC_` filename prefix
and `data_kind=SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS` in every row. Their original
numeric text and row ordering are unchanged. The four reader tables retain their
existing marking; the two renderer tables gain the same marking.

The frozen renderer4040 itself is unchanged. On synthetic inputs only, it writes
to a fresh temporary staging directory. The outer wrapper checks every original
receipt hash, then stores the complete unchanged original output and original
receipt as exact members of `SYNTHETIC_UPSTREAM_RENDERER_ORIGINALS.zip`. This ZIP
is a historical lineage archive, **not the usable derived CSV export**. Its
original receipt applies only to original archive members.

The visible `rendered/` folder contains the marked derived CSVs and unchanged,
already-watermarked graphs. Its new `render_receipt.json` hashes those actual
derived files separately. `upstream_lineage` records the ZIP SHA, its relative
path from the derived receipt, every exact original-member SHA, and the exact
original receipt member/SHA. `csv_derivations` maps each derived table to its
original archive member and explains the added mark. No original receipt is
misrepresented as describing changed CSV bytes.

The original rendering bytes are never modified. Temporary staging is cleaned
only after the original files and receipt have been archived and verified.
The production branch runs the identical previous subprocess statement and
does not invoke this wrapper. The notebook cells, frozen4040 renderer, reader3d08,
math, production binding rules and optional native gate are unchanged.

Focused checks use the already-created synthetic renderer outputs and the
previously verified synthetic cache; they generate no bootstrap draws, model
steps or new feeding results. The passed v1 fresh-kernel, discovery and core
integration proofs are retained as v1 proofs. No v2 native or production-data
certification is claimed. The final validation profile remains PENDING.
