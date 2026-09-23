"""Phần (c): kiểm `ranking.csv` và đánh giá proxy sau khi khóa xếp hạng (lab-design §6.4).

Proxy = số lỗi model thật KHÁC NHAU mà batch đã chọn trỏ vào, trên chi phí. Cùng một xe bị model sai cùng kiểu ở
nhiều frame liền nhau chỉ tính một lần: gán nhãn lại nó ở frame thứ hai gần như không dạy model thêm gì.
Lỗi ở frame ngoại lai (lóa, xe chỉ còn vài pixel) được đếm riêng, không vào số chính: model sai ở đó thật, nhưng gán
nhãn frame đó gần như không dạy được gì (lab-design §6.2). Proxy không đo model sau khi học có tốt hơn không.
"""
import csv
import os
import random

from . import data
from .data import LabError

FLAGS = ("ok", "duplicate", "outlier")
PROXY_LIMIT = ("Proxy này đo lựa chọn có trỏ vào chỗ model sai hay không; "
               "nó không đo model sau khi học có tốt hơn không.")
N_RANDOM = 1000


def budget():
    return data.load_json(os.path.join(data.DATA, "pool", "budget.json"))


def frame_costs(scenario):
    """Chi phí từng frame theo kịch bản: S1 = 1 frame; S2 = số box model thấy (dòng trong pool_predictions.csv)."""
    frames = data.pool_frames()
    if scenario == "S1":
        return {f: 1 for f in frames}
    n = {f: 0 for f in frames}
    for r in data.pool_predictions():
        n[r["frame_id"]] += 1
    return n


def read_ranking():
    path = data.sub("ranking.csv")
    if not os.path.exists(path):
        raise LabError("Thiếu submission/ranking.csv")
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if (r.get("frame_id") or "").strip()]


def validate_ranking(info):
    rows = read_ranking()
    frames = set(data.pool_frames())
    ids = [r["frame_id"].strip() for r in rows]
    problems = []
    if sorted(ids) != sorted(frames):
        miss, extra = sorted(frames - set(ids)), sorted(set(ids) - frames)
        dup = sorted({i for i in ids if ids.count(i) > 1})
        problems.append(f"cần đúng 50 frame pool, mỗi frame một dòng (thiếu {miss[:5]}, thừa {extra[:5]}, trùng {dup[:5]})")
    try:
        ranks = sorted(int(r["rank"]) for r in rows)
        if ranks != list(range(1, len(rows) + 1)):
            problems.append("rank phải là 1…50, không trùng")
    except (KeyError, ValueError):
        problems.append("cột rank phải là số nguyên")
    bad_flag = sorted({r.get("flag", "").strip() for r in rows} - set(FLAGS))
    if bad_flag:
        problems.append(f"flag chỉ nhận {'/'.join(FLAGS)} (gặp: {bad_flag})")
    sel = [r["frame_id"].strip() for r in rows if (r.get("selected") or "").strip() == "1"]
    cost = frame_costs(info["scenario"])
    spent = sum(cost.get(f, 0) for f in sel)
    b = budget()[info["scenario"]]["budget"]
    if not sel:
        problems.append("chưa đánh selected = 1 cho batch gửi gán nhãn")
    if spent > b:
        problems.append(f"batch đã chọn tốn {spent} > ngân sách {b} ({info['scenario']})")
    if problems:
        raise LabError("ranking.csv chưa hợp lệ:\n  - " + "\n  - ".join(problems))
    return rows, sel, spent


def frame_scores(scenario):
    """Bảng hỗ trợ (đường Support): least confidence 1 − conf gộp ba cách, cộng margin nhỏ nhất cho stretch.
    Không xếp hạng và không chọn hộ: chọn cách gộp, loại trùng, gắn cờ vẫn là việc của học viên."""
    frames, cost = data.pool_frames(), frame_costs(scenario)
    boxes = {f: [] for f in frames}
    for r in data.pool_predictions():
        boxes[r["frame_id"]].append(r)
    out = []
    for f in sorted(frames):
        lc = [1 - float(r["conf"]) for r in boxes[f]]
        margin = [float(r["p_top1"]) - float(r["p_top2"]) for r in boxes[f] if (r.get("p_top2") or "").strip()]
        fr = frames[f]
        out.append(dict(frame_id=f, seq_id=fr["seq_id"], camera_id=fr["camera_id"], time_s=fr["time_s"],
                        n_boxes=len(lc), cost=cost[f], sum_lc=round(sum(lc), 4),
                        mean_lc=round(sum(lc) / len(lc), 4) if lc else 0.0, max_lc=round(max(lc), 4) if lc else 0.0,
                        min_margin=round(min(margin), 4) if margin else ""))
    return out


def cmd_frame_scores(args):
    info = data.info()
    rows = frame_scores(info["scenario"])
    with open(data.sub("frame_scores.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    b = budget()[info["scenario"]]["budget"]
    print(f"Đã ghi submission/frame_scores.csv: {len(rows)} frame, điểm 1 − conf gộp sum / mean / max, cột cost theo {info['scenario']} "
          f"(ngân sách {b}).")
    print("Bảng này chưa phải xếp hạng: bạn chọn một cách gộp và nói vì sao, rồi loại trùng + gắn cờ ngoại lai trước khi lấy top.")


def fill(order, cost, b):
    """Đi theo thứ tự, lấy frame nào còn vừa ngân sách."""
    out, spent = [], 0
    for f in order:
        if spent + cost[f] <= b:
            out.append(f); spent += cost[f]
    return out


def naive_topk(cost, b):
    score = {f: 0.0 for f in cost}
    for r in data.pool_predictions():
        score[r["frame_id"]] += 1 - float(r["conf"])
    return fill(sorted(cost, key=lambda f: -score[f]), cost, b)


def distinct_errors(sel, err):
    return len({k for f in sel for k in err[f]["error_keys"]})


def learnable_errors(sel, err):
    """Số chính của proxy: lỗi khác nhau, bỏ frame ngoại lai."""
    return distinct_errors([f for f in sel if err[f]["category"] != "outlier"], err)


def own_score_no_dedup(rows, cost, b):
    """Phản thực tế: giữ nguyên điểm frame của học viên, bỏ bước sampling (không loại trùng, không bỏ cờ).
    None nếu cột frame_score chưa phải số ở mọi dòng."""
    try:
        score = {r["frame_id"].strip(): float(r["frame_score"]) for r in rows}
        rank = {r["frame_id"].strip(): int(r["rank"]) for r in rows}
    except (KeyError, TypeError, ValueError):
        return None
    return fill(sorted(score, key=lambda f: (-score[f], rank[f])), cost, b)


def describe(sel, err, cost, frames):
    return dict(n_frames=len(sel), cost=sum(cost[f] for f in sel), errors=learnable_errors(sel, err), errors_all=distinct_errors(sel, err),
                errors_raw=sum(err[f]["n_errors"] for f in sel),
                real_boxes=sum(err[f]["n_ref_boxes"] for f in sel), scenes=len({frames[f]["seq_id"] for f in sel}),
                cameras=len({frames[f]["camera_id"] for f in sel}),
                categories={c: sum(err[f]["category"] == c for f in sel) for c in sorted({v["category"] for v in err.values()})})


def cmd_al_eval(args):
    from .lock import _verify
    info = data.info()
    _verify("lock_ranking.txt")
    rows, sel, _ = validate_ranking(info)
    err = data.pool_errors()["frames"]
    frames = data.pool_frames()
    cost = frame_costs(info["scenario"])
    b = budget()[info["scenario"]]["budget"]
    rng = random.Random(8)
    rand = []
    for _ in range(N_RANDOM):
        order = list(cost); rng.shuffle(order)
        rand.append(learnable_errors(fill(order, cost, b), err))
    rand.sort()
    mine, naive = describe(sel, err, cost, frames), describe(naive_topk(cost, b), err, cost, frames)
    nodup = own_score_no_dedup(rows, cost, b)
    nodup = describe(nodup, err, cost, frames) if nodup is not None else None
    below = sum(x < mine["errors"] for x in rand) / N_RANDOM
    unit = "frame" if info["scenario"] == "S1" else "box ước tính"
    print(f"== al-eval — kịch bản {info['scenario']}, ngân sách {b} {unit}")
    cols = [("của bạn", mine)] + ([("điểm bạn, bỏ sampling", nodup)] if nodup else []) + [("sum, không loại trùng", naive)]
    print(f"{'':<26}" + "".join(f"{c:>24}" for c, _ in cols))
    for label, k in (("frame được chọn", "n_frames"), (f"chi phí ({unit})", "cost"), ("box thật phải vẽ", "real_boxes"),
                     ("lỗi khác nhau (số chính)", "errors"), ("  + gồm frame ngoại lai", "errors_all"),
                     ("lỗi cộng theo frame", "errors_raw"), ("số video khác nhau", "scenes"), ("số camera khác nhau", "cameras")):
        print(f"  {label:<24}" + "".join(f"{d[k]:>24}" for _, d in cols))
    print(f"  {'lỗi / chi phí':<24}" + "".join(f"{d['errors'] / max(1, d['cost']):>24.2f}" for _, d in cols))
    print("  Số chính = lỗi model khác nhau, không tính frame ngoại lai (sai thật nhưng gán nhãn không dạy được gì).")
    print("  \"cộng theo frame\" > \"khác nhau\" = batch gán nhãn lại cùng một lỗi ở nhiều frame gần nhau.")
    if nodup:
        print("  \"điểm bạn, bỏ sampling\" = cùng frame_score của bạn, lấy thẳng từ cao xuống: chênh với cột đầu là phần "
              "bước loại trùng/gắn cờ của bạn đóng góp.")
    else:
        print("  (frame_score chưa phải số ở mọi dòng nên không tách được phần đóng góp của bước sampling)")
    print(f"\n  {N_RANDOM} lần chọn ngẫu nhiên: trung vị {rand[N_RANDOM // 2]} lỗi, khoảng 5–95% "
          f"[{rand[int(.05 * N_RANDOM)]}, {rand[int(.95 * N_RANDOM)]}]; batch của bạn cao hơn {100 * below:.0f}% số lần ngẫu nhiên")
    print(f"  Thành phần batch của bạn theo loại frame (Lab Coach thiết kế pool): {mine['categories']}")
    print(f"  Thành phần sum, không loại trùng                                    : {naive['categories']}")
    print(f"\n{PROXY_LIMIT}")
    data.write_json(data.sub("al_eval.json"), dict(scenario=info["scenario"], budget=b, mine=mine, own_score_no_dedup=nodup, naive_topk=naive,
                   random=dict(median=rand[N_RANDOM // 2], p05=rand[int(.05 * N_RANDOM)], p95=rand[int(.95 * N_RANDOM)],
                               share_below_mine=round(below, 3)), limit=PROXY_LIMIT))
