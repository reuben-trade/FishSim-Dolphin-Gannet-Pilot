"""Saved-data accounting checks. Run: python -m unittest discover -s tools/replay_viewer."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.replay_viewer.loader import build_catalog, load_case, validate_source
from tools.replay_viewer.metrics import compare_runs, percent_change


class SavedRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = build_catalog()
        cls.cases = {row["id"]: row for row in cls.bundle["scenarios"]}

    def test_declared_108_cases_and_no_duplicate_pilot(self):
        self.assertEqual(len(self.cases), 108)
        self.assertEqual(sum(row["gannet_count"] in (9, 12, 18) for row in self.cases.values()), 48)
        self.assertEqual({row["school_seed"] for row in self.cases.values()}, {39061001, 39061002, 39063501, 39063502})

    def test_neutral_default_capture_mask_and_counters(self):
        row = self.cases["s39063501_H2_G6_DG_c61001"]
        data = load_case(row["source"], row)
        self.assertEqual(len(data["times"]), 361)
        self.assertEqual(data["times"][-1], 36)
        self.assertEqual(sum(v for k, v in data["final_counts"].items() if k.startswith("D")), 25)
        self.assertEqual(sum(v for k, v in data["final_counts"].items() if k.startswith("G")), 16)
        self.assertEqual(data["final_count"], 119)
        for frame, positions in enumerate(data["positions"]):
            captured = {event["prey_id"] for event in data["captures"] if event["frame_index"] <= frame}
            dead = {prey for prey, point in zip(data["prey_ids"], positions) if point == [None, None, None]}
            self.assertEqual(captured, dead)
        self.assertIsNone(data["body_radii"])

    def test_high_count_replays_and_species_matched_controls(self):
        row = self.cases["s39063501_H2_G18_DG_c61001"]
        data = load_case(row["source"], row)
        self.assertEqual(len(data["actor_ids"]), 30)
        self.assertEqual(data["final_count"], 103)
        self.assertIsNone(row["matched_controls"]["D"]["reference_id"])
        self.assertEqual(row["matched_controls"]["G"]["reference_id"], "s39063501_Gonly18_G_c61001")

    def test_cross_study_and_cross_school_percentages_disabled(self):
        a = self.cases["s39063501_H2_G18_DG_c61001"]["summary"]
        b = self.cases["s39063501_H2_G0_D_c61001"]["summary"]
        comp = compare_runs(a, b)
        self.assertFalse(comp["matched"])
        self.assertIsNone(comp["species"]["D"]["rate_percent_change"])
        c = self.cases["s39063502_H2_G0_D_c61001"]["summary"]
        self.assertFalse(compare_runs(b, c)["matched"])

    def test_known_gain_uses_full_horizon_per_predator_rate(self):
        row = self.cases["s39063502_H2_G1_DG_c61001"]
        self.assertAlmostEqual(row["matched_controls"]["D"]["rate_percent_change"], 100 * 3 / 22)
        self.assertEqual(row["matched_controls"]["G"]["rate_percent_change"], 0)
        self.assertIsNone(percent_change(0, 0)["value"])

    def test_changed_packaged_artifact_rejected(self):
        source = Path(self.cases[self.bundle["default_ids"][0]]["source"])
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for path in source.iterdir():
                if path.is_file() and path.name != "config.json":
                    (directory / path.name).symlink_to(path)
            config = json.loads((source / "config.json").read_text())
            config["viewer_test_tamper"] = True
            (directory / "config.json").write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "differs from its seal: config.json"):
                validate_source(directory)


if __name__ == "__main__":
    unittest.main()
