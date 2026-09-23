import json
import os
import shutil
import tempfile
import types
import unittest
import warnings
import zipfile

warnings.simplefilter("ignore", ResourceWarning)
_showwarning = warnings.showwarning


def _hide_resource_warning(message, category, filename, lineno, file=None, line=None):
    if issubclass(category, ResourceWarning):
        return
    _showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = _hide_resource_warning

from lab8 import cvatxml, data, lock, review
from lab8.data import LabError


def box(cls, x1, y1, x2, y2):
    return {"cls": cls, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def ref(kind, x1, y1, x2, y2):
    return {"type": kind, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


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
        for path in (data.DATA, data.REF, data.SUB):
            os.makedirs(path, exist_ok=True)


class ReviewTests(LabDataPatchMixin, unittest.TestCase):
    def test_assess_frame_marks_residual_and_new_errors(self):
        must = [
            ref("car", 0, 0, 10, 10),
            ref("bus", 20, 0, 30, 10),
            ref("car", 40, 0, 50, 10),
        ]
        pre = [
            box("car", 0, 0, 10, 10),
            box("car", 20, 0, 30, 10),
            box("car", 40, 0, 50, 10),
            box("car", 100, 0, 110, 10),
        ]
        post = [
            box("car", 0, 0, 10, 10),
            box("car", 20, 0, 30, 10),
            box("car", 100, 0, 110, 10),
            box("car", 120, 0, 130, 10),
        ]

        got = review.assess_frame(pre, post, must, [])

        self.assertEqual([o["ai"] for o in got["objects"]], ["ok", "cls", "ok"])
        self.assertEqual([o["me"] for o in got["objects"]], ["ok", "cls", "fn"])
        self.assertEqual([o["residual"] for o in got["objects"]], [False, True, False])
        self.assertEqual([o["new"] for o in got["objects"]], [False, False, True])
        self.assertEqual(got["ai_fp"], [3])
        self.assertEqual(got["fp_residual"], [3])
        self.assertEqual(got["added_fp"], [3])

    def test_honeypot_result_separates_omission_and_commission(self):
        must = [ref("car", 0, 0, 10, 10), ref("bus", 20, 0, 30, 10)]
        key = {
            "edits": [
                {"type": "omission", "removed": dict(must[0])},
                {"type": "commission", "box": dict(must[1])},
            ]
        }
        post = [box("car", 0, 0, 10, 10), box("car", 20, 0, 30, 10)]

        self.assertEqual(
            review.honeypot_result(key, post, must, []),
            {"omission": True, "commission": False},
        )

    def test_build_profile_counts_shared_miss(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            os.makedirs(os.path.join(data.DATA, "prelabel"))
            os.makedirs(os.path.join(data.DATA, "pool"))

            with open(os.path.join(data.DATA, "manifest.csv"), "w", encoding="utf-8") as f:
                f.write("frame_id,set,condition,file,sha256,width,height,n_prelabel\n")
                f.write("x01,X,sunny,frames/lab/x01.jpg,,100,100,0\n")
                f.write("y01,Y,sunny,frames/lab/y01.jpg,,100,100,0\n")
                f.write("c01,C,rainy,frames/lab/c01.jpg,,100,100,2\n")
            pre = {
                "x01": [],
                "y01": [],
                "c01": [box("car", 0, 0, 10, 10), box("bus", 20, 0, 30, 10)],
            }
            with open(os.path.join(data.DATA, "prelabel", "prelabel.json"), "w", encoding="utf-8") as f:
                json.dump({"frames": pre}, f)
            reference = {
                "x01": {"condition": "sunny", "must": [ref("car", 0, 0, 10, 10)], "dontcare": []},
                "y01": {"condition": "sunny", "must": [ref("car", 0, 0, 10, 10)], "dontcare": []},
                "c01": {
                    "condition": "rainy",
                    "must": [ref("car", 0, 0, 10, 10), ref("bus", 20, 0, 30, 10)],
                    "dontcare": [],
                },
            }
            with open(os.path.join(data.REF, "reference.json"), "w", encoding="utf-8") as f:
                json.dump({"frames": reference}, f)
            with open(os.path.join(data.REF, "honeypot_key.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "frame_id": "c01",
                        "edits": [
                            {"type": "omission", "removed": dict(reference["c01"]["must"][0])},
                            {"type": "commission", "box": dict(reference["c01"]["must"][1])},
                        ],
                    },
                    f,
                )
            sizes = {"x01.jpg": (100, 100), "y01.jpg": (100, 100), "c01.jpg": (100, 100)}
            cvatxml.write(data.sub("manual_X.xml"), [("x01.jpg", [])], sizes)
            cvatxml.write(
                data.sub("assisted.xml"),
                [("c01.jpg", pre["c01"]), ("y01.jpg", [])],
                sizes,
            )

            got = review.build_profile({"group": "A"}, data.sub("assisted.xml"))

            self.assertEqual(got["tot"]["model_missed"], 1)
            self.assertEqual(got["tot"]["shared_missed"], 1)
            self.assertEqual(got["man"]["model_missed"], 1)
            self.assertEqual(got["man"]["shared_missed"], 1)
            self.assertEqual(got["by_set"]["Y"]["shared_missed"], 1)


class CvatXmlTests(unittest.TestCase):
    def test_write_read_round_trip_keeps_boxes_and_classes(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "ann.xml")
            frames = [("a01.jpg", [box("car", 1, 2, 11, 22), box("bus", 30, 40, 50, 60)])]
            cvatxml.write(path, frames, {"a01.jpg": (100, 80)})

            got = cvatxml.read(path)

            self.assertEqual([b["cls"] for b in got["a01"]["boxes"]], ["car", "bus"])
            self.assertEqual(got["a01"]["boxes"][0]["x1"], 1.0)
            self.assertEqual(got["a01"]["size"], (100, 80))

    def test_read_keeps_not_reviewed_tag(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "tagged.xml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    '<?xml version="1.0" encoding="utf-8"?>\n'
                    "<annotations><image id=\"0\" name=\"assisted/c01.jpg\" width=\"10\" height=\"10\">"
                    '<tag label="not_reviewed"></tag>'
                    '<box label="car" xtl="0" ytl="0" xbr="5" ybr="5"></box>'
                    "</image></annotations>\n"
                )

            got = cvatxml.read(path)

            self.assertIn(cvatxml.NOT_REVIEWED, got["c01"]["tags"])


class LockTests(LabDataPatchMixin, unittest.TestCase):
    def test_verify_lock_fails_after_tamper(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            with open(data.sub("states.json"), "w", encoding="utf-8") as f:
                f.write("{}\n")
            lock._write_lock("lock.txt", ["states.json"])
            with open(data.sub("states.json"), "w", encoding="utf-8") as f:
                f.write('{"tampered": true}\n')

            with self.assertRaises(LabError):
                lock.verify_lock()

    def test_install_reference_refuses_before_lock(self):
        with tempfile.TemporaryDirectory() as root:
            self.point_data_at(root)
            zip_path = os.path.join(root, "reference_pack.zip")
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("reference.json", "{}")

            with self.assertRaises(LabError):
                lock.cmd_install_reference(types.SimpleNamespace(zip=zip_path))


if __name__ == "__main__":
    unittest.main()
