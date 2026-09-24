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
        self.assertEqual(rows["p001"]["ai_priority"], 1)
        self.assertEqual(rows["p001"]["ai_suggested"], 1)
        self.assertEqual(rows["p003"]["ai_suggested"], 0)  # No detection is not proof of an empty scene.

    def test_frame_scores_prefills_only_blank_ranking(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_pool()
            data.write_json(data.sub("info.json"), {"name": "Tester", "group": "A", "scenario": "S1"})
            self.write_ranking([dict(frame_id=fid, rank="", frame_score="", selected="0", flag="ok", reason="")
                                for fid in ("p001", "p002", "p003")])
            with contextlib.redirect_stdout(io.StringIO()):
                ranking.cmd_frame_scores(types.SimpleNamespace())
            rows = ranking.read_ranking()
            self.assertEqual(sorted(int(r["rank"]) for r in rows), [1, 2, 3])
            self.assertTrue(any(r["selected"] == "1" for r in rows))
            rows[0]["reason"] = "Tôi đã kiểm ảnh"
            self.write_ranking(rows)
            with contextlib.redirect_stdout(io.StringIO()):
                ranking.cmd_frame_scores(types.SimpleNamespace())
            self.assertEqual(ranking.read_ranking()[0]["reason"], "Tôi đã kiểm ảnh")

    def test_frame_scores_preserves_partial_work_even_without_ranks(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_pool()
            data.write_json(data.sub("info.json"), {"name": "Tester", "group": "A", "scenario": "S1"})
            self.write_ranking([dict(frame_id=fid, rank="", frame_score="", selected="0", flag="ok",
                                     reason="đã xem ảnh" if fid == "p001" else "")
                                for fid in ("p001", "p002", "p003")])
            with contextlib.redirect_stdout(io.StringIO()):
                ranking.cmd_frame_scores(types.SimpleNamespace())
            self.assertEqual(ranking.read_ranking()[0]["reason"], "đã xem ảnh")
            self.assertEqual(ranking.read_ranking()[0]["rank"], "")


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
            self.assertEqual(workspace.copy_after_lock_templates(), ["reflection.md", "case_review.md", "next_round.md"])
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
        self.assertEqual(workspace._filled("## Top 5\n1.\n2.\n"), [])
        self.assertEqual(workspace._field_answers("Frame và vật: c01 xe đỏ <!-- ví dụ -->\n"), {"Frame và vật": "c01 xe đỏ"})
        self.assertEqual(workspace._field_answers("Frame và vật: <!-- chỉ dẫn -->\n"), {"Frame và vật": ""})

    def test_verify_data_passes_on_shipped_data(self):
        with contextlib.redirect_stdout(io.StringIO()):
            workspace.cmd_verify_data(types.SimpleNamespace())

    def test_optional_partner_does_not_change_case_or_next_round_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            self.write_minimal_data()
            with open(os.path.join(data.DATA, "pool", "pool_frames.csv"), "a", encoding="utf-8") as f:
                for fid in ("p002", "p003", "p004"):
                    f.write(f"{fid},S02,K02,2,1,frames/pool/{fid}.jpg\n")
            with open(os.path.join(data.DATA, "pool", "budget.json"), "w", encoding="utf-8") as f:
                json.dump({"S1": {"budget": 2}}, f)
            with open(data.sub("ranking.csv"), "w", encoding="utf-8") as f:
                f.write("frame_id,rank,frame_score,selected,flag,reason\n")
                f.write("p001,1,0.9,1,ok,first\n")
                for i, fid in enumerate(("p002", "p003", "p004"), 2):
                    f.write(f"{fid},{i},0.4,0,ok,remaining\n")
            workspace.copy_after_lock_templates()
            info = {"scenario": "S1"}
            errors = workspace._check_core(info)
            self.assertTrue(any("case_review.md" in e for e in errors))
            self.assertTrue(any("next_round.md" in e for e in errors))
            with open(data.sub("case_review.md"), "w", encoding="utf-8") as f:
                for key in ("Chế độ", "Frame và vật", "Quyết định độc lập ban đầu", "Góc nhìn thứ hai",
                            "Bằng chứng theo guideline", "Kết luận và sửa/giữ", "Tuyến xử lý lần sau"):
                    f.write(f"{key}: " + ("c01 xe trái" if key == "Frame và vật" else "bằng chứng cụ thể") + "\n")
            with open(data.sub("next_round.md"), "w", encoding="utf-8") as f:
                for key in ("Tín hiệu từ lượt 1", "Điểm yếu của gợi ý AI ban đầu", "Ba frame chưa chọn cho lượt sau",
                            "Vì sao ba frame bổ trợ nhau", "Quy tắc tôi sẽ đổi", "Giới hạn"):
                    f.write(f"{key}: " + ("p002, p003, p004" if key.startswith("Ba frame") else "lý do cụ thể") + "\n")
            errors = workspace._check_core(info)
            self.assertFalse(any("case_review.md" in e or "next_round.md" in e for e in errors))
            with open(data.sub("next_round.md"), "r+", encoding="utf-8") as f:
                text = f.read().replace("p002, p003, p004", "p001, p003, p004")
                f.seek(0); f.write(text); f.truncate()
            self.assertTrue(any("next_round.md" in e for e in workspace._check_core(info)))


if __name__ == "__main__":
    unittest.main()
