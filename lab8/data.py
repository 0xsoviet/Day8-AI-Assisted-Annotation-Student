"""Đường dẫn và nạp dữ liệu của repo học viên. Mọi lệnh đọc từ đây để không lệch nhau về tên file."""
import csv
import hashlib
import json
import os

ROOT = os.environ.get("LAB8_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
REF = os.path.join(ROOT, "reference")
SUB = os.environ.get("LAB8_SUBMISSION") or os.path.join(ROOT, "submission")

# Đối chứng chéo (lab-design §5.1): khối tay luôn trước khối có AI.
GROUPS = {"A": {"manual": "X", "assisted": ("Y", "C")},
          "B": {"manual": "Y", "assisted": ("X", "C")}}
SCENARIOS = ("S1", "S2")


class LabError(Exception):
    """Lỗi người dùng sửa được; CLI in thông điệp tiếng Việt thay vì traceback."""


def load_json(path, what=None):
    if not os.path.exists(path):
        raise LabError(f"Thiếu {what or path}: {os.path.relpath(path, ROOT)}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def manifest():
    with open(os.path.join(DATA, "manifest.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lab_frames():
    """{frame_id: {"set": X|Y|C|demo, "condition": ...}} cho 17 frame lab."""
    return {r["frame_id"]: r for r in manifest() if r["set"] in ("X", "Y", "C", "demo")}


def frames_of(*sets):
    return sorted(fid for fid, r in lab_frames().items() if r["set"] in sets)


def prelabel():
    return load_json(os.path.join(DATA, "prelabel", "prelabel.json"))["frames"]


def pool_frames():
    with open(os.path.join(DATA, "pool", "pool_frames.csv"), encoding="utf-8") as f:
        return {r["frame_id"]: r for r in csv.DictReader(f)}


def pool_predictions():
    with open(os.path.join(DATA, "pool", "pool_predictions.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def info():
    d = load_json(os.path.join(SUB, "info.json"), "submission/info.json (chạy `make init` trước)")
    if d.get("group") not in GROUPS:
        raise LabError("submission/info.json: group phải là A hoặc B")
    return d


def reference():
    return load_json(os.path.join(REF, "reference.json"),
                     "reference (Lab Coach phát sau khi bạn khóa bài; cài bằng `make install-reference ZIP=...`)")["frames"]


def honeypot_key():
    return load_json(os.path.join(REF, "honeypot_key.json"), "key honeypot (đi cùng gói reference)")


def pool_errors():
    return load_json(os.path.join(REF, "pool_errors.json"),
                     "lỗi model trên pool (gói 2, Lab Coach phát sau khi bạn khóa xếp hạng)")


def sub(name):
    return os.path.join(SUB, name)


def manual_file(group):
    return sub(f"manual_{GROUPS[group]['manual']}.xml")
