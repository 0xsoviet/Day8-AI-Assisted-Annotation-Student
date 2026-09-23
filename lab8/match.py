"""Hai phép ghép của lab.

- `states`: bản sửa ↔ pre-label đóng băng → accepted / edited / deleted / added. Không cần reference.
- `evaluate`: một bộ box ↔ reference (must / dontcare) → trạng thái từng vật và từng box.
"""
from .geom import iou, ACCEPT_IOU, LOC_IOU, MATCH_IOU


def _greedy(pairs):
    """pairs: [(key..., i, j)] đã sắp giảm dần; mỗi i, j dùng tối đa một lần."""
    used_i, used_j, out = set(), set(), []
    for p in pairs:
        i, j = p[-2], p[-1]
        if i in used_i or j in used_j:
            continue
        used_i.add(i); used_j.add(j); out.append(p)
    return out, used_i, used_j


def states(pre, post):
    """Ghép pre-label với bản sửa ở IoU ≥ 0,3, ưu tiên cùng class rồi IoU cao.

    0,3 (không phải 0,5): học viên sửa một box lệch vị trí về đúng chỗ thì box mới có thể chỉ còn IoU 0,3–0,5 với box
    cũ; ở 0,5 thao tác đó bị đếm thành deleted + added (POC P3 §2.2).
    Trả về danh sách dict {state, pre, post, iou}; pre/post là chỉ số hoặc None.
    """
    pairs = sorted(((p["cls"] == q["cls"], iou(p, q), i, j)
                    for i, p in enumerate(pre) for j, q in enumerate(post) if iou(p, q) >= LOC_IOU), reverse=True)
    matched, used_i, used_j = _greedy(pairs)
    rows = [dict(state="accepted" if same and v >= ACCEPT_IOU else "edited", pre=i, post=j, iou=round(v, 3))
            for same, v, i, j in matched]
    rows += [dict(state="deleted", pre=i, post=None, iou=None) for i in range(len(pre)) if i not in used_i]
    rows += [dict(state="added", pre=None, post=j, iou=None) for j in range(len(post)) if j not in used_j]
    return rows


def evaluate(boxes, must, dontcare):
    """So một bộ box với reference, dontcare không tính FN cũng không tính FP.

    Vật (must): ok | cls (đúng chỗ, sai class) | loc (IoU 0,3–0,5) | fn (không có box nào).
    Box: ok | cls | loc | dc (trùng vùng dontcare, không tính) | dup (box thừa trên vật đã có box) | fp.
    Trả về (obj, box): obj[k] = (status, chỉ số box, iou); box[i] = (status, chỉ số vật, iou).
    """
    obj = [("fn", None, 0.0)] * len(must)
    box = [None] * len(boxes)
    pairs = sorted(((b["cls"] == g["type"], iou(b, g), i, k)
                    for i, b in enumerate(boxes) for k, g in enumerate(must) if iou(b, g) >= MATCH_IOU), reverse=True)
    matched, used_b, used_g = _greedy(pairs)
    for same, v, i, k in matched:
        s = "ok" if same else "cls"
        obj[k] = (s, i, round(v, 3)); box[i] = (s, k, round(v, 3))
    loose = sorted(((iou(boxes[i], must[k]), i, k) for i in range(len(boxes)) if i not in used_b
                    for k in range(len(must)) if k not in used_g and iou(boxes[i], must[k]) >= LOC_IOU), reverse=True)
    lmatched, lb, lg = _greedy(loose)
    for v, i, k in lmatched:
        obj[k] = ("loc", i, round(v, 3)); box[i] = ("loc", k, round(v, 3))
    for i, b in enumerate(boxes):
        if box[i] is not None:
            continue
        if any(iou(b, d) >= LOC_IOU for d in dontcare):
            box[i] = ("dc", None, 0.0)
        elif any(iou(b, g) >= MATCH_IOU for g in must):
            box[i] = ("dup", max(range(len(must)), key=lambda k: iou(b, must[k])), 0.0)
        else:
            box[i] = ("fp", None, 0.0)
    return obj, box
