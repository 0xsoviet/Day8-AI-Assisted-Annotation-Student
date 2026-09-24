"""Tạo thư mục nộp, kiểm dữ liệu phát, kiểm gói nộp. Không chấm điểm: chỉ báo thiếu gì và file nào sai dạng."""
import csv
import os
import re
import shutil

from . import data
from .data import LabError

TEMPLATES = os.path.join(data.ROOT, "templates")
TEMPLATE_FILES = ("decision_log.csv", "prediction.md", "interpretation.md", "ranking_rationale.md", "peer_check.md")
# Câu phản tư nói thẳng giả thuyết đo (bỏ sót theo AI), nên chỉ tạo sau khi khóa bài — xem `copy_after_lock_templates`.
AFTER_LOCK_TEMPLATES = ("reflection.md", "case_review.md", "next_round.md")
CAUSES = ("rule_unclear", "missed_search", "anchored", "tool_slip", "reference_disputed")
LOG_STATES = ("accepted", "edited", "deleted", "added", "escalated", "not_reviewed", "out-of-schema")


def cmd_init(args):
    from .assignment import assignment_for, normalize_user

    name = (args.name or "").strip()
    github_user = normalize_user(getattr(args, "github_user", "")) if getattr(args, "github_user", None) else ""
    if github_user:
        group, scenario = assignment_for(github_user)
    else:
        group = (getattr(args, "group", "") or "").strip().upper()
        scenario = (getattr(args, "scenario", "") or "").strip().upper()
    if not name or group not in data.GROUPS or scenario not in data.SCENARIOS:
        raise LabError("Cần: make init NAME=\"Họ Tên\" GITHUB_USER=tai-khoan-github")
    os.makedirs(data.SUB, exist_ok=True)
    path = data.sub("info.json")
    if os.path.exists(path):
        old = data.load_json(path)
        if (old.get("group"), old.get("scenario")) != (group, scenario):
            raise LabError(f"submission/info.json đã có nhóm {old.get('group')}, kịch bản {old.get('scenario')}. "
                           "Không đổi tài khoản giữa buổi; giữ nguyên bài đang làm.")
        if github_user and old.get("github_user") not in (None, github_user):
            raise LabError("submission/info.json thuộc tài khoản GitHub khác; không đổi tài khoản giữa buổi.")
    info = dict(name=name, group=group, scenario=scenario)
    if github_user:
        info["github_user"] = github_user
    data.write_json(path, info)
    made = []
    for n in TEMPLATE_FILES:
        if not os.path.exists(data.sub(n)):
            shutil.copy(os.path.join(TEMPLATES, n), data.sub(n)); made.append(n)
    if not os.path.exists(data.sub("ranking.csv")):
        with open(data.sub("ranking.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["frame_id", "rank", "frame_score", "selected", "flag", "reason"])
            for fid in sorted(data.pool_frames()):
                w.writerow([fid, "", "", "0", "ok", ""])
        made.append("ranking.csv")
    g = data.GROUPS[group]
    print(f"Chào {name}. Lộ trình {group}: khối tay = tập {g['manual']} ({len(data.frames_of(g['manual']))} frame), "
          f"khối có AI = tập {' + '.join(g['assisted'])} ({len(data.frames_of(*g['assisted']))} frame). Kịch bản chi phí {scenario}.")
    print("Đã tạo trong submission/: " + (", ".join(made) or "(không có file mới — giữ nguyên bài đang làm)"))


def copy_after_lock_templates():
    made = []
    for n in AFTER_LOCK_TEMPLATES:
        if not os.path.exists(data.sub(n)):
            shutil.copy(os.path.join(TEMPLATES, n), data.sub(n)); made.append(n)
    return made


def cmd_verify_data(args):
    sums = os.path.join(data.DATA, "SHA256SUMS")
    bad, n = [], 0
    for line in data.read_text(sums).splitlines():
        h, _, rel = line.strip().partition("  ")
        if not rel:
            continue
        n += 1
        p = os.path.join(data.DATA, rel)
        if not os.path.exists(p):
            bad.append(f"thiếu {rel}")
        elif data.sha256(p) != h:
            bad.append(f"khác sha256: {rel}")
    if bad:
        raise LabError("Dữ liệu không khớp bản phát (tải lại repo, đừng sửa data/):\n  " + "\n  ".join(bad[:20]))
    print(f"data/ khớp SHA256SUMS: {n} file.")


# ---------------------------------------------------------------- check-submission

def _rows(name):
    p = data.sub(name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]


def _text(name):
    p = data.sub(name)
    return data.read_text(p) if os.path.exists(p) else None


def _filled(text):
    """Bỏ comment HTML và dòng hướng dẫn của template; còn chữ thật thì coi là đã viết."""
    body = re.sub(r"<!--.*?-->", "", text or "", flags=re.S)
    return [l for l in body.splitlines() if l.strip() and not l.lstrip().startswith(("#", ">", "|---"))
            and not re.fullmatch(r"\d+\.", l.strip())]


def _field_answers(text):
    """Các dòng 'Trường: câu trả lời' sau khi bỏ hướng dẫn ẩn trong template."""
    return {key.strip(): value.strip() for line in _filled(text)
            if ":" in line for key, value in [line.split(":", 1)]}


def _check_min(info):
    """Mục 1–4 (§7): bắt buộc tối thiểu cho mọi người."""
    out = []
    for n in (os.path.basename(data.manual_file(info["group"])), "assisted.xml"):
        if not os.path.exists(data.sub(n)):
            out.append(f"thiếu {n}")
    log = _rows("decision_log.csv")
    if log is None:
        out.append("thiếu decision_log.csv")
    else:
        mine = [r for r in log if (r.get("frame_id") or "").strip() != "d01"]
        need = ("frame_id", "object", "state", "rule_or_reason", "found_before_ai_toggle", "signed_by")
        incomplete = [i + 2 for i, r in enumerate(log) if r in mine and any(not (r.get(k) or "").strip() for k in need)]
        states_bad = sorted({r["state"].strip() for r in mine if (r.get("state") or "").strip() not in LOG_STATES})
        if len(mine) < 5:
            out.append(f"decision_log.csv có {len(mine)} dòng của bạn (không tính dòng mẫu d01), cần ≥ 5")
        if incomplete:
            out.append(f"decision_log.csv dòng {incomplete[:8]} còn cột trống")
        if states_bad:
            out.append(f"decision_log.csv: state không hợp lệ {states_bad} (dùng {'/'.join(LOG_STATES)})")
    for n in ("states.json", "prediction.md", "lock.txt"):
        if not os.path.exists(data.sub(n)):
            out.append(f"thiếu {n}" + (" — chạy make lock" if n == "lock.txt" else ""))
    if os.path.exists(data.sub("lock.txt")):
        from .lock import verify_lock
        try:
            verify_lock()
        except LabError as e:
            out.append(str(e))
    return out


def _check_core(info):
    """Mục 5–8 (§7): core; hết giờ thì Lab Coach ghi nhận và cho nộp bổ sung."""
    out = []
    if not os.path.exists(data.sub("error_profile.csv")):
        out.append("thiếu error_profile.csv — chạy make profile sau khi cài reference")
    lines = _filled(_text("interpretation.md"))
    if len(lines) < 4:
        out.append("interpretation.md chưa viết (cần 1 dòng lệch dự đoán + 3 phát hiện)")
    elif not any(re.search(r"\d+\s*/\s*\d+", l) for l in lines):
        out.append("interpretation.md: phát hiện cần tử số/mẫu số (vd 4/9)")
    rw = _rows("rework_log.csv")
    if rw is None:
        out.append("thiếu rework_log.csv — make profile tạo sẵn")
    else:
        bad = [i + 2 for i, r in enumerate(rw) if (r.get("cause") or "").strip() not in CAUSES or not (r.get("action") or "").strip()]
        if bad:
            out.append(f"rework_log.csv dòng {bad[:8]}: cần cause ∈ {'/'.join(CAUSES)} và action")
        if not os.path.exists(data.sub("assisted_rework.xml")):
            out.append("thiếu assisted_rework.xml (export bản đã sửa lại; chép assisted.xml nếu không có gì để sửa)")
    try:
        from .ranking import validate_ranking
        validate_ranking(info)
    except LabError as e:
        out.append(str(e))
    if not os.path.exists(data.sub("frame_scores.csv")):
        out.append("thiếu frame_scores.csv — chạy make frame-scores")
    if not os.path.exists(data.sub("al_eval.json")):
        out.append("thiếu al_eval.json — chạy make al-eval sau khi cài gói 2")
    for n in ("ranking_rationale.md", "peer_check.md"):
        if len(_filled(_text(n))) < 3:
            out.append(f"{n} chưa viết")
    case = _field_answers(_text("case_review.md"))
    if len([v for v in case.values() if v]) < 7 or not re.search(r"\bc0[1-4]\b", case.get("Frame và vật", "")):
        out.append("case_review.md cần đủ 7 trường và một frame C cụ thể")
    next_round = _field_answers(_text("next_round.md"))
    ids = re.findall(r"\bp\d{3}\b", next_round.get("Ba frame chưa chọn cho lượt sau", ""))
    selected = {r["frame_id"].strip() for r in read_ranking_safe() if (r.get("selected") or "").strip() == "1"}
    if len([v for v in next_round.values() if v]) < 6 or len(set(ids)) != 3 or set(ids) & selected or not set(ids) <= set(data.pool_frames()):
        out.append("next_round.md cần đủ 6 trường và 3 frame pool khác nhau, chưa chọn ở lượt 1")
    if not os.path.exists(data.sub("lock_ranking.txt")):
        out.append("chưa khóa xếp hạng (make lock-ranking)")
    else:
        from .lock import _verify
        try:
            _verify("lock_ranking.txt")
        except LabError as e:
            out.append(str(e))
    refl = _text("reflection.md")
    if refl is None:
        out.append("thiếu reflection.md — make profile tạo sẵn sau khi cài reference")
        return out
    answered = sum(bool(_filled(part)) for part in re.split(r"^##\s*Câu\s*\d.*$", refl, flags=re.M)[1:])
    if answered < 4:
        out.append(f"reflection.md: trả lời {answered}/4 câu")
    return out


def read_ranking_safe():
    """Đọc ranking để kiểm kế hoạch vòng sau; lỗi định dạng đã được báo bởi validate_ranking."""
    from .ranking import read_ranking
    try:
        return read_ranking()
    except (LabError, UnicodeError, csv.Error):
        return []


def cmd_check_submission(args):
    info = data.info()
    need, core = _check_min(info), _check_core(info)
    print(f"== Gói nộp của {info.get('name', '?')} (nhóm {info['group']}, {info['scenario']})")
    print("\nMục 1–4 — bắt buộc tối thiểu:")
    print("  đủ" if not need else "\n".join("  ✗ " + x for x in need))
    print("\nMục 5–8 — core (thiếu thì báo Lab Coach, nộp bổ sung trước buổi sau):")
    print("  đủ" if not core else "\n".join("  ✗ " + x.replace("\n", "\n    ") for x in core))
    print("\nLệnh này chỉ kiểm có đủ và đúng dạng; không chấm điểm.")
    if need:
        raise SystemExit(1)
