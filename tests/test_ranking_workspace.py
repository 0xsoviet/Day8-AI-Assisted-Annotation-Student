import csv
import contextlib
import io
import json
import os
import tempfile
import types
import unittest
import warnings

warnings.simplefilter("ignore", ResourceWarning)
_showwarning = warnings.showwarning


def _hide_resource_warning(message, category, filename, lineno, file=None, line=None):
    if issubclass(category, ResourceWarning):
        return
    _showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = _hide_resource_warning

from lab8 import data, ranking, workspace
from lab8.assignment import assignment_for
from lab8.data import LabError


class LabDataPatchMixin:
    def setUp(self):
        self._old_paths = data.ROOT, data.DATA, data.REF, data.SUB

    def tearDown(self):
        data.ROOT, data.DATA, data.REF, data.SUB = self._old_paths

    def point_data_at(self, root):
        data.ROOT = root
        data.DATA = os.path.join(root, "data")
        data.REF = os.path.join(root, "reference")
        data.SUB = os.path.join(root, "submission")
        os.makedirs(os.path.join(data.DATA, "pool"), exist_ok=True)
        os.makedirs(data.SUB, exist_ok=True)


class RankingTests(LabDataPatchMixin, unittest.TestCase):
    def write_pool(self):
        with open(os.path.join(data.DATA, "pool", "pool_frames.csv"), "w", encoding="utf-8") as f:
            f.write("frame_id,seq_id,camera_id,frame_idx,time_s,file\n")
            for fid in ("p001", "p002", "p003"):
                f.write(f"{fid},S01,K01,1,0,frames/pool/{fid}.jpg\n")
        with open(os.path.join(data.DATA, "pool", "pool_predictions.csv"), "w", encoding="utf-8") as f:
            f.write("frame_id,conf\n")
            f.write("p001,0.9\np002,0.8\np002,0.7\np003,0.6\n")
        with open(os.path.join(data.DATA, "pool", "budget.json"), "w", encoding="utf-8") as f:
            json.dump({"S1": {"budget": 2}, "S2": {"budget": 3}}, f)

    def write_ranking(self, rows):
        with open(data.sub("ranking.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["frame_id", "rank", "frame_score", "selected", "flag", "reason"])
            w.writeheader()
            w.writerows(rows)

    def test_validate_ranking_catches_bad_inputs(self):
        cases = [
            (
                "missing_duplicate",
                [
                    {"frame_id": "p001", "rank": "1", "selected": "1", "flag": "ok"},
                    {"frame_id": "p001", "rank": "2", "selected": "0", "flag": "ok"},
                    {"frame_id": "p002", "rank": "3", "selected": "0", "flag": "ok"},
                ],
                "thiếu",
            ),
            (
                "bad_rank",
                [
                    {"frame_id": "p001", "rank": "1", "selected": "1", "flag": "ok"},
                    {"frame_id": "p002", "rank": "1", "selected": "0", "flag": "ok"},
                    {"frame_id": "p003", "rank": "3", "selected": "0", "flag": "ok"},
                ],
                "rank",
            ),
            (
                "bad_flag",
                [
                    {"frame_id": "p001", "rank": "1", "selected": "1", "flag": "bad"},
                    {"frame_id": "p002", "rank": "2", "selected": "0", "flag": "ok"},
                    {"frame_id": "p003", "rank": "3", "selected": "0", "flag": "ok"},
                ],
                "flag",
            ),
            (
                "over_budget",
                [
                    {"frame_id": "p001", "rank": "1", "selected": "1", "flag": "ok"},
                    {"frame_id": "p002", "rank": "2", "selected": "1", "flag": "ok"},
                    {"frame_id": "p003", "rank": "3", "selected": "1", "flag": "ok"},
                ],
                "ngan sach".replace("ngan sach", "ngân sách"),
            ),
        ]
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_pool()
            for name, rows, expected in cases:
                with self.subTest(name=name):
                    self.write_ranking(rows)
                    with self.assertRaises(LabError) as cm:
                        ranking.validate_ranking({"scenario": "S1"})
                    self.assertIn(expected, str(cm.exception))

    def test_fill_respects_budget(self):
        got = ranking.fill(["f1", "f2", "f3"], {"f1": 2, "f2": 3, "f3": 1}, 3)
        self.assertEqual(got, ["f1", "f3"])  # f2 is skipped so f3 still fits exactly.

    def test_distinct_errors_counts_repeated_key_once(self):
        err = {
            "a": {"error_keys": ["S01:gt:5:fn"]},
            "b": {"error_keys": ["S01:gt:5:fn"]},
        }
        self.assertEqual(ranking.distinct_errors(["a", "b"], err), 1)

    def test_frame_scores_aggregates_least_confidence_per_frame(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_pool()
            with open(os.path.join(data.DATA, "pool", "pool_predictions.csv"), "w", encoding="utf-8") as f:
                f.write("frame_id,conf,p_top1,p_top2\n")
                f.write("p001,0.9,0.9,0.1\np001,0.5,0.5,0.4\np002,0.8,0.8,\n")
            rows = {r["frame_id"]: r for r in ranking.frame_scores("S2")}
        self.assertEqual(rows["p001"]["cost"], 2)  # S2 pays per predicted box.
        self.assertAlmostEqual(rows["p001"]["sum_lc"], 0.6)  # 0.1 + 0.5.
        self.assertAlmostEqual(rows["p001"]["mean_lc"], 0.3)
        self.assertAlmostEqual(rows["p001"]["max_lc"], 0.5)
        self.assertAlmostEqual(rows["p001"]["min_margin"], 0.1)
        self.assertEqual(rows["p002"]["min_margin"], "")  # No second class score, no margin.
        self.assertEqual((rows["p003"]["n_boxes"], rows["p003"]["mean_lc"]), (0, 0.0))  # Empty frame does not divide by zero.


class WorkspaceTests(LabDataPatchMixin, unittest.TestCase):
    def write_minimal_data(self):
        with open(os.path.join(data.DATA, "manifest.csv"), "w", encoding="utf-8") as f:
            f.write("frame_id,set,condition,file,sha256,width,height,n_prelabel\n")
            f.write("x01,X,sunny,frames/lab/x01.jpg,,100,100,0\n")
            f.write("y01,Y,sunny,frames/lab/y01.jpg,,100,100,0\n")
            f.write("c01,C,sunny,frames/lab/c01.jpg,,100,100,0\n")
        with open(os.path.join(data.DATA, "pool", "pool_frames.csv"), "w", encoding="utf-8") as f:
            f.write("frame_id,seq_id,camera_id,frame_idx,time_s,file\n")
            f.write("p001,S01,K01,1,0,frames/pool/p001.jpg\n")

    def test_init_creates_templates_and_refuses_group_change(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_minimal_data()
            args = types.SimpleNamespace(name="Tester", group="A", scenario="S1")

            with contextlib.redirect_stdout(io.StringIO()):
                workspace.cmd_init(args)

            self.assertTrue(os.path.exists(data.sub("info.json")))
            self.assertTrue(os.path.exists(data.sub("prediction.md")))
            self.assertTrue(os.path.exists(data.sub("ranking.csv")))
            # Câu phản tư nói thẳng giả thuyết đo: chỉ được tạo sau khi khóa bài.
            self.assertFalse(os.path.exists(data.sub("reflection.md")))
            self.assertEqual(workspace.copy_after_lock_templates(), ["reflection.md"])
            self.assertTrue(os.path.exists(data.sub("reflection.md")))
            with self.assertRaises(LabError):
                workspace.cmd_init(types.SimpleNamespace(name="Tester", group="B", scenario="S1"))

    def test_github_user_assigns_stable_route_without_coach_input(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_minimal_data()
            args = types.SimpleNamespace(name="Tester", github_user="@Student-08", group=None, scenario=None)
            with contextlib.redirect_stdout(io.StringIO()):
                workspace.cmd_init(args)
            info = data.info()
            self.assertEqual(info["github_user"], "student-08")
            self.assertEqual((info["group"], info["scenario"]), assignment_for("student-08"))
            with contextlib.redirect_stdout(io.StringIO()):
                workspace.cmd_init(args)
            with self.assertRaises(LabError):
                workspace.cmd_init(types.SimpleNamespace(name="Tester", github_user="someone-else", group=None, scenario=None))

    def test_filled_ignores_template_comments(self):
        text = "# Heading\n<!-- hidden answer -->\n> prompt\n|---|---|\nReal answer 4/9\n"
        self.assertEqual(workspace._filled(text), ["Real answer 4/9"])

    def test_verify_data_passes_on_shipped_data(self):
        with contextlib.redirect_stdout(io.StringIO()):
            workspace.cmd_verify_data(types.SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
