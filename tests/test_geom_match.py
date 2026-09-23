import unittest
import warnings

warnings.simplefilter("ignore", ResourceWarning)
_showwarning = warnings.showwarning


def _hide_resource_warning(message, category, filename, lineno, file=None, line=None):
    if issubclass(category, ResourceWarning):
        return
    _showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = _hide_resource_warning

from lab8 import geom, match


def box(cls, x1, y1, x2, y2):
    return {"cls": cls, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def ref(kind, x1, y1, x2, y2):
    return {"type": kind, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


class GeometryTests(unittest.TestCase):
    def test_iou(self):
        a = box("car", 0, 0, 10, 10)
        b = box("car", 5, 5, 15, 15)
        self.assertAlmostEqual(geom.iou(a, b), 1 / 7)  # 25 intersection / 175 union.

    def test_size_bucket_boundaries(self):
        self.assertEqual(geom.size_bucket(box("car", 0, 0, 31, 33)), "small")  # 1023 < 32^2.
        self.assertEqual(geom.size_bucket(box("car", 0, 0, 32, 32)), "medium")  # 32^2 is medium.
        self.assertEqual(geom.size_bucket(box("car", 0, 0, 95, 96)), "medium")  # 9120 < 96^2.
        self.assertEqual(geom.size_bucket(box("car", 0, 0, 96, 96)), "large")  # 96^2 is large.


class MatchStateTests(unittest.TestCase):
    def test_states_cover_all_labels(self):
        pre = [
            box("car", 0, 0, 10, 10),
            box("bus", 20, 0, 30, 10),
            box("van", 40, 0, 50, 10),
            box("car", 70, 0, 80, 10),
        ]
        post = [
            box("car", 0, 0, 10, 10),
            box("car", 20, 0, 30, 10),
            box("others", 100, 0, 110, 10),
        ]
        rows = match.states(pre, post)
        states = {(r["state"], r["pre"], r["post"]) for r in rows}
        self.assertIn(("accepted", 0, 0), states)
        self.assertIn(("edited", 1, 1), states)  # Same place, class changed.
        self.assertIn(("deleted", 2, None), states)
        self.assertIn(("added", None, 2), states)

    def test_states_greedy_pairing_uses_best_iou_once(self):
        pre = [box("car", 0, 0, 10, 10)]
        post = [box("car", 1, 0, 11, 10), box("car", 0, 0, 10, 10)]
        rows = sorted(match.states(pre, post), key=lambda r: (r["state"], r["post"] or -1))
        self.assertEqual(rows[0]["state"], "accepted")
        self.assertEqual(rows[0]["post"], 1)
        self.assertEqual(rows[0]["iou"], 1.0)  # Exact box beats the shifted 9/11 IoU box.
        self.assertEqual(rows[1]["state"], "added")
        self.assertEqual(rows[1]["post"], 0)


class EvaluateTests(unittest.TestCase):
    def test_evaluate_object_and_box_error_types(self):
        must = [
            ref("car", 0, 0, 10, 10),
            ref("bus", 20, 0, 30, 10),
            ref("van", 40, 0, 50, 10),
            ref("car", 60, 0, 70, 10),
        ]
        dontcare = [ref("car", 200, 0, 210, 10)]
        boxes = [
            box("car", 0, 0, 10, 10),
            box("car", 20, 0, 30, 10),
            box("van", 45, 0, 55, 10),
            box("car", 0, 0, 9, 10),
            box("car", 100, 0, 110, 10),
            box("car", 200, 0, 210, 10),
        ]

        obj, got_box = match.evaluate(boxes, must, dontcare)

        self.assertEqual([o[0] for o in obj], ["ok", "cls", "loc", "fn"])
        self.assertEqual([b[0] for b in got_box], ["ok", "cls", "loc", "dup", "fp", "dc"])
        self.assertEqual(obj[2][2], 0.333)  # 50 intersection / 150 union.


if __name__ == "__main__":
    unittest.main()
