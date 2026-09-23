"""Khóa bài bằng hash trước khi mở đáp án; cài gói reference sau khi khóa."""
import datetime
import hashlib
import os
import zipfile

from . import data
from .data import LabError

PART1 = ("assisted.xml", "decision_log.csv", "prediction.md", "states.json")   # + manual_<set>.xml
PART2 = ("ranking.csv", "ranking_rationale.md", "peer_check.md")
PACKS = {"reference.json": "lock.txt", "honeypot_key.json": "lock.txt", "pool_errors.json": "lock_ranking.txt"}


def _sha(path):
    return data.sha256(path)


def _write_lock(lock_name, names):
    lock = data.sub(lock_name)
    if os.path.exists(lock):
        raise LabError(f"submission/{lock_name} đã có — bài đã khóa. Mọi sửa đổi sau khóa đi vào bản rework, không khóa lại.")
    missing = [n for n in names if not os.path.exists(data.sub(n))]
    if missing:
        raise LabError("Chưa đủ file để khóa: " + ", ".join(missing))
    lines = [f"{_sha(data.sub(n))}  {n}" for n in names]
    combined = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(lock, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + f"\ncombined  {combined}\nlocked_at  {stamp}\n")
    return combined


def _verify(lock_name):
    lock = data.sub(lock_name)
    if not os.path.exists(lock):
        raise LabError(f"Chưa khóa (thiếu submission/{lock_name}).")
    for line in data.read_text(lock).splitlines():
        h, _, name = line.strip().partition("  ")
        if name and h not in ("combined", "locked_at"):
            if not os.path.exists(data.sub(name)) or _sha(data.sub(name)) != h:
                raise LabError(f"submission/{name} đã đổi sau khi khóa. Trả lại bản đã khóa; sửa đổi mới đi vào bản rework.")


def verify_lock():
    _verify("lock.txt")


def cmd_lock(args):
    from .review import read_prediction
    if os.path.exists(os.path.join(data.REF, "reference.json")):
        raise LabError("reference đã cài trong repo này — không khóa sau khi đã có đáp án.")
    pr = read_prediction()
    missing = [k for k in ("accept_rate_pct", "honeypot_caught", "my_missed_objects") if k not in pr]
    if missing:
        raise LabError("prediction.md chưa điền đủ 3 số: " + ", ".join(missing))
    combined = _write_lock("lock.txt", [os.path.basename(data.manual_file(data.info()["group"]))] + list(PART1))
    print(f"Đã khóa phần (a)+(b). Gửi mã này cho Lab Coach: {combined[:12]}")


def cmd_lock_ranking(args):
    from .ranking import validate_ranking
    validate_ranking(data.info())
    combined = _write_lock("lock_ranking.txt", list(PART2))
    print(f"Đã khóa xếp hạng. Gửi mã này cho Lab Coach: {combined[:12]}")


def cmd_install_reference(args):
    if not args.zip or not os.path.exists(args.zip):
        raise LabError("Cần đường dẫn gói: make install-reference ZIP=<file.zip>")
    with zipfile.ZipFile(args.zip) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        unknown = [n for n in names if os.path.basename(n) not in PACKS]
        if unknown or not names:
            raise LabError("Gói không đúng: " + ", ".join(unknown or ["(rỗng)"]))
        for n in names:
            _verify(PACKS[os.path.basename(n)])
        os.makedirs(data.REF, exist_ok=True)
        for n in names:
            with open(os.path.join(data.REF, os.path.basename(n)), "wb") as f:
                f.write(z.read(n))
    print("Đã cài: " + ", ".join(sorted(os.path.basename(n) for n in names)))
