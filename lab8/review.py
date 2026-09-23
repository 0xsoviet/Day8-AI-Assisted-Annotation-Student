"""Phần (a)+(b): 4 trạng thái (trước khi mở reference) và error profile (sau khi mở reference).

Định nghĩa đo nằm ở lab-design §5.2; file này chỉ hiện thực chúng.
"""
import csv
import os
import re

from . import cvatxml, data
from .data import LabError
from .geom import size_bucket
from .match import evaluate, states

STATES = ("accepted", "edited", "deleted", "added")


def read_export(path, frames, what):
    if not os.path.exists(path):
        raise LabError(f"Thiếu {what}: {os.path.relpath(path, data.ROOT)} (export job từ CVAT, định dạng 'CVAT for images 1.1')")
    try:
        got = cvatxml.read(path)
    except (ValueError, Exception) as e:  # noqa: BLE001 — XML hỏng hoặc sai định dạng: báo lại cho học viên
        raise LabError(f"Không đọc được {os.path.relpath(path, data.ROOT)}: {e}")
    missing = sorted(set(frames) - set(got))
    if missing:
        raise LabError(f"{os.path.relpath(path, data.ROOT)} thiếu frame {', '.join(missing)} — export nhầm job?")
    bad = sorted({b["cls"] for f in frames for b in got[f]["boxes"]} - {"car", "van", "bus", "others"})
    if bad:
        raise LabError(f"{os.path.relpath(path, data.ROOT)} có label ngoài schema: {', '.join(bad)}")
    return {f: got[f] for f in frames}


def assisted_frames(group):
    return data.frames_of(*data.GROUPS[group]["assisted"])


def manual_frames(group):
    return data.frames_of(data.GROUPS[group]["manual"])


# ---------------------------------------------------------------- states

def compute_states(group, xml_path):
    pre = data.prelabel()
    lab = data.lab_frames()
    got = read_export(xml_path, assisted_frames(group), "bản export job có AI")
    out, skipped = {}, []
    for fid, fr in got.items():
        if cvatxml.NOT_REVIEWED in fr["tags"]:
            skipped.append(fid)
            continue
        rows = states(pre[fid], fr["boxes"])
        for r in rows:
            r["cls"] = pre[fid][r["pre"]]["cls"] if r["pre"] is not None else fr["boxes"][r["post"]]["cls"]
            if r["state"] == "edited":
                r["cls_after"] = fr["boxes"][r["post"]]["cls"]
        out[fid] = dict(condition=lab[fid]["condition"], rows=rows)
    return out, skipped


def summarize_states(frames):
    count = {s: 0 for s in STATES}
    by = {}
    for fid, fr in frames.items():
        for r in fr["rows"]:
            count[r["state"]] += 1
            cell = by.setdefault(f'{r["cls"]}|{fr["condition"]}', {s: 0 for s in STATES})
            cell[r["state"]] += 1
    n_pre = count["accepted"] + count["edited"] + count["deleted"]
    n_final = count["accepted"] + count["edited"] + count["added"]
    return dict(counts=count, n_prelabel=n_pre, n_final=n_final,
                accept_rate=round(count["accepted"] / n_pre, 3) if n_pre else None,
                added_share=round(count["added"] / n_final, 3) if n_final else None,
                by_class_condition=dict(sorted(by.items())))


def cmd_states(args):
    info = data.info()
    frames, skipped = compute_states(info["group"], data.sub("assisted.xml"))
    summary = summarize_states(frames)
    data.write_json(data.sub("states.json"), dict(group=info["group"], not_reviewed=skipped, summary=summary, frames=frames))
    c = summary["counts"]
    print(f"Nhóm {info['group']}: {len(frames)} frame đã duyệt, {len(skipped)} frame not_reviewed {skipped or ''}")
    print(f"  accepted {c['accepted']} · edited {c['edited']} · deleted {c['deleted']} · added {c['added']}")
    print(f"  accept rate = {c['accepted']}/{summary['n_prelabel']} = {pct(summary['accept_rate'])}"
          f" · added / box cuối = {c['added']}/{summary['n_final']} = {pct(summary['added_share'])}")
    print("\n  class|lát            accepted edited deleted added")
    for k, v in summary["by_class_condition"].items():
        print(f"  {k:<18}{v['accepted']:>8}{v['edited']:>7}{v['deleted']:>8}{v['added']:>6}")
    print("\nĐã ghi submission/states.json. Số này mô tả hành vi sửa, chưa nói đúng hay sai.")


# ---------------------------------------------------------------- profile

def _obj_id(k, g):
    return f"o{k + 1}@{int(g['x1'])},{int(g['y1'])}"


def assess_frame(pre, post, must, dc):
    """Một frame có AI: lỗi AI, residual, new error, lỗi của người sửa. Trả về danh sách sự kiện theo vật/box."""
    obj_p, box_p = evaluate(pre, must, dc)
    obj_q, box_q = evaluate(post, must, dc)
    link = {r["pre"]: r["post"] for r in states(pre, post) if r["pre"] is not None and r["post"] is not None}
    objects = []
    for k, g in enumerate(must):
        ai, me = obj_p[k][0], obj_q[k][0]
        objects.append(dict(k=k, cls=g["type"], size=size_bucket(g), ai=ai, me=me,
                            residual=ai != "ok" and me != "ok", new=ai == "ok" and me != "ok"))
    ai_fp = [i for i, b in enumerate(box_p) if b[0] in ("fp", "dup")]
    fp_residual = [i for i in ai_fp if i in link and box_q[link[i]][0] in ("fp", "dup")]
    linked_post = set(link.values())
    my_fp = [j for j, b in enumerate(box_q) if b[0] in ("fp", "dup")]
    added_fp = [j for j in my_fp if j not in linked_post]
    return dict(objects=objects, ai_fp=ai_fp, fp_residual=fp_residual, added_fp=added_fp, my_fp=my_fp)


def honeypot_result(key, post_frame, must, dc):
    from .geom import iou
    out = {}
    obj_q, _ = evaluate(post_frame, must, dc) if post_frame is not None else ([("fn", None, 0)] * len(must), [])
    for e in key["edits"]:
        b = e["removed"] if e["type"] == "omission" else e["box"]
        k = max(range(len(must)), key=lambda k: iou(b, must[k]))
        out[e["type"]] = obj_q[k][0] == "ok"
    return out


def read_prediction():
    path = data.sub("prediction.md")
    if not os.path.exists(path):
        return {}
    got = {}
    for key in ("accept_rate_pct", "honeypot_caught", "my_missed_objects"):
        m = re.search(rf"^\s*{key}\s*:\s*([0-9]+(?:[.,][0-9]+)?)", data.read_text(path), re.M)
        if m:
            got[key] = float(m.group(1).replace(",", "."))
    return got


def decision_log_rows():
    path = data.sub("decision_log.csv")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if (r.get("frame_id") or "").strip()]


def build_profile(info, xml_path):
    group = info["group"]
    ref, pre, lab = data.reference(), data.prelabel(), data.lab_frames()
    got = read_export(xml_path, assisted_frames(group), "bản export job có AI")
    manual = read_export(data.manual_file(group), manual_frames(group), "bản làm tay")
    hp = data.honeypot_key()
    cells, errors = {}, []
    tot = dict(ai_obj_err=0, ai_fp=0, residual=0, fp_residual=0, ai_ok=0, new=0, added_fp=0,
               n_obj=0, my_missed=0, model_missed=0, shared_missed=0)
    skipped = []
    by_set = {}

    def set_row(fid, mode):
        return by_set.setdefault(lab[fid]["set"], dict(mode=mode, n_obj=0, my_missed=0, model_missed=0, shared_missed=0))

    def cell(kind, value, cls):
        return cells.setdefault((kind, value, cls), dict(
            n_objects_assisted=0, ai_fn=0, ai_cls=0, ai_loc=0, my_residual=0, my_new=0, my_missed_assisted=0,
            n_objects_manual=0, my_missed_manual=0, model_missed_manual=0, my_missed_of_model_missed_manual=0))

    for fid in assisted_frames(group):
        if cvatxml.NOT_REVIEWED in got[fid]["tags"]:
            skipped.append(fid)
            continue
        r = ref[fid]
        a = assess_frame(pre[fid], got[fid]["boxes"], r["must"], r["dontcare"])
        for o in a["objects"]:
            g = r["must"][o["k"]]
            for kind, value in (("condition", r["condition"]), ("size", o["size"])):
                c = cell(kind, value, o["cls"])
                c["n_objects_assisted"] += 1
                if o["ai"] in ("fn", "cls", "loc"):
                    c["ai_" + o["ai"]] += 1
                c["my_residual"] += o["residual"]
                c["my_new"] += o["new"]
                c["my_missed_assisted"] += o["me"] == "fn"
            tot["n_obj"] += 1
            tot["ai_obj_err"] += o["ai"] != "ok"
            tot["residual"] += o["residual"]
            tot["ai_ok"] += o["ai"] == "ok"
            tot["new"] += o["new"]
            tot["my_missed"] += o["me"] == "fn"
            tot["model_missed"] += o["ai"] == "fn"
            tot["shared_missed"] += o["ai"] == "fn" and o["me"] == "fn"
            s = set_row(fid, "assisted")
            s["n_obj"] += 1; s["my_missed"] += o["me"] == "fn"
            s["model_missed"] += o["ai"] == "fn"; s["shared_missed"] += o["ai"] == "fn" and o["me"] == "fn"
            if o["me"] != "ok":
                errors.append(dict(frame_id=fid, object=_obj_id(o["k"], g), ref_class=o["cls"], error=o["me"],
                                   origin="residual" if o["residual"] else "new"))
        post = got[fid]["boxes"]
        for j in a["added_fp"]:
            b = post[j]
            errors.append(dict(frame_id=fid, object=f"box@{int(b['x1'])},{int(b['y1'])}", ref_class="-",
                               error="fp", origin="added"))
        for i in a["fp_residual"]:
            b = pre[fid][i]
            errors.append(dict(frame_id=fid, object=f"box@{int(b['x1'])},{int(b['y1'])}", ref_class="-",
                               error="fp", origin="residual"))
        tot["ai_fp"] += len(a["ai_fp"])
        tot["fp_residual"] += len(a["fp_residual"])
        tot["added_fp"] += len(a["added_fp"])

    man = dict(n_obj=0, missed=0, model_missed=0, shared_missed=0)
    for fid in manual_frames(group):
        r = ref[fid]
        obj_m, _ = evaluate(manual[fid]["boxes"], r["must"], r["dontcare"])
        obj_p, _ = evaluate(pre[fid], r["must"], r["dontcare"])
        for k, g in enumerate(r["must"]):
            miss, mm = obj_m[k][0] == "fn", obj_p[k][0] == "fn"
            for kind, value in (("condition", r["condition"]), ("size", size_bucket(g))):
                c = cell(kind, value, g["type"])
                c["n_objects_manual"] += 1
                c["my_missed_manual"] += miss
                c["model_missed_manual"] += mm
                c["my_missed_of_model_missed_manual"] += miss and mm
            man["n_obj"] += 1; man["missed"] += miss; man["model_missed"] += mm; man["shared_missed"] += miss and mm
            s = set_row(fid, "manual")
            s["n_obj"] += 1; s["my_missed"] += miss; s["model_missed"] += mm; s["shared_missed"] += miss and mm

    hp_frame = hp["frame_id"]
    hp_post = None if hp_frame in skipped else got[hp_frame]["boxes"]
    honeypot = honeypot_result(hp, hp_post, ref[hp_frame]["must"], ref[hp_frame]["dontcare"])
    return dict(cells=cells, errors=errors, tot=tot, man=man, by_set=by_set, honeypot=honeypot, skipped=skipped,
                honeypot_skipped=hp_post is None)


def ratio(a, b):
    return f"{a}/{b} = {pct(a / b)}" if b else f"{a}/0 = —"


def pct(x):
    return "—" if x is None else f"{100 * x:.0f}%"


def cmd_profile(args):
    from .lock import verify_lock
    info = data.info()
    verify_lock()
    rework = getattr(args, "rework", False)
    base = build_profile(info, data.sub("assisted.xml"))
    if rework:
        return print_rework(info, base)
    st = data.load_json(data.sub("states.json"))["summary"]
    t, m, hp = base["tot"], base["man"], base["honeypot"]

    with open(data.sub("error_profile.csv"), "w", newline="", encoding="utf-8") as f:
        cols = ["slice_kind", "slice", "class"] + list(next(iter(base["cells"].values())).keys())
        w = csv.writer(f); w.writerow(cols)
        for (kind, value, cls), c in sorted(base["cells"].items()):
            w.writerow([kind, value, cls] + list(c.values()))
    if not os.path.exists(data.sub("rework_log.csv")):
        with open(data.sub("rework_log.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["frame_id", "object", "ref_class", "error", "origin", "cause", "action", "note"])
            w.writeheader()
            for e in base["errors"]:
                w.writerow(dict(e, cause="", action="", note=""))
        made = True
    else:
        made = False

    print(f"== Error profile — nhóm {info['group']}, {len(base['skipped'])} frame not_reviewed {base['skipped'] or ''}")
    print("\n[1] Lỗi của AI trên batch có AI của bạn (pre-label so với reference)")
    print(f"    vật model làm sai (fn/cls/loc): {ratio(t['ai_obj_err'], t['n_obj'])}; box bịa (fp): {t['ai_fp']}")
    print("\n[2] Bạn sau khi thẩm định")
    print(f"    residual error rate (lỗi AI còn lại)    : {ratio(t['residual'] + t['fp_residual'], t['ai_obj_err'] + t['ai_fp'])}")
    print(f"    new error rate (AI đúng, bạn sửa thành sai): {ratio(t['new'], t['ai_ok'])}")
    print(f"    box bạn tự thêm nhưng không có vật      : {t['added_fp']}")
    print("\n[3] Bạn làm tay vs có AI — vật MODEL bỏ sót")
    print(f"    có AI : bạn cũng bỏ sót {ratio(t['shared_missed'], t['model_missed'])}  (shared-miss)")
    print(f"    làm tay: bạn bỏ sót    {ratio(m['shared_missed'], m['model_missed'])}  (cùng loại vật, trên tập làm tay)")
    print(f"    mọi vật — có AI bỏ sót {ratio(t['my_missed'], t['n_obj'])} · làm tay bỏ sót {ratio(m['missed'], m['n_obj'])}")
    print("    Hai tập khác frame và khác thứ tự làm → đây là tín hiệu, không phải kết luận.")
    print("\n[4] Honeypot (1 frame, 2 lỗi cài)" + (" — frame honeypot bạn đánh not_reviewed" if base["honeypot_skipped"] else ""))
    print(f"    omission (box bị xóa)     : {'bắt được' if hp['omission'] else 'lọt'}")
    print(f"    commission (class bị đổi) : {'bắt được' if hp['commission'] else 'lọt'}")
    log = decision_log_rows()
    af = set(assisted_frames(info["group"]))
    alog = [r for r in log if r["frame_id"].strip() in af]
    yes = sum((r.get("found_before_ai_toggle") or "").strip().lower() in ("yes", "có", "co", "1", "y") for r in alog)
    print(f"\n[5] decision_log: {len(alog)} dòng ở khối có AI, found_before_ai_toggle = có: {ratio(yes, len(alog))} (tự khai)")
    pr = read_prediction()
    actual = dict(accept_rate_pct=round(100 * (st["accept_rate"] or 0)), honeypot_caught=sum(hp.values()),
                  my_missed_objects=t["my_missed"])
    print("\n[6] Dự đoán (trong prediction.md, đã khóa) vs thực tế")
    for k, v in actual.items():
        g = pr.get(k)
        print(f"    {k:<18} đoán {'—' if g is None else f'{g:g}':>5} · thật {v:>4}" + ("" if g is None else f" · lệch {v - g:+g}"))
    data.write_json(data.sub("profile.json"), dict(group=info["group"], tot=t, manual=m, by_set=base["by_set"], honeypot=hp, not_reviewed=base["skipped"],
                   prediction=pr, actual=actual, decision_log=dict(rows=len(alog), found_before_ai_toggle=yes)))
    print(f"\nĐã ghi submission/error_profile.csv + profile.json (class × lát, bỏ qua ô chỉ có 1–2 vật khi rút kết luận).")
    from .workspace import copy_after_lock_templates
    for n in copy_after_lock_templates():
        print(f"Đã tạo submission/{n} (4 câu phản tư, trả lời ở phút 220).")
    if made:
        print(f"Đã tạo submission/rework_log.csv với {len(base['errors'])} lỗi của bạn — điền cause/action cho từng dòng.")
    print("Nhắc: accept rate không phải chất lượng; một frame honeypot không đủ để xếp hạng người.")


def print_rework(info, base):
    path = data.sub("assisted_rework.xml")
    after = build_profile(info, path)
    b, a = base["tot"], after["tot"]
    print("== Trước / sau vòng sửa lại (phép đo bias vẫn tính trên bản đã khóa)")
    for label, key in (("vật bạn bỏ sót (có AI)", "my_missed"), ("residual (vật)", "residual"),
                       ("new error", "new"), ("box thừa bạn thêm", "added_fp")):
        print(f"    {label:<24} {b[key]:>3} → {a[key]:>3}")
    hb, ha = base["honeypot"], after["honeypot"]
    print(f"    honeypot bắt được          {sum(hb.values())} → {sum(ha.values())}")
    log = data.sub("rework_log.csv")
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        empty = sum(not (r.get("cause") or "").strip() for r in rows)
        print(f"    rework_log: {len(rows)} dòng, {empty} dòng chưa có cause")
