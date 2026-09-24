"""CLI: python3 -m lab8 <lệnh>. Lỗi người dùng sửa được in một dòng tiếng Việt, không in traceback."""
import argparse
import sys

from .data import LabError
from . import lock, ranking, review, workspace

COMMANDS = {
    "init": (workspace.cmd_init, "tạo submission/ và các template"),
    "verify-data": (workspace.cmd_verify_data, "kiểm data/ khớp SHA256SUMS"),
    "states": (review.cmd_states, "4 trạng thái từ assisted.xml (trước khi có reference)"),
    "lock": (lock.cmd_lock, "khóa phần (a)+(b) bằng hash, gồm prediction.md"),
    "install-reference": (lock.cmd_install_reference, "cài gói reference Lab Coach phát (ZIP=...)"),
    "profile": (review.cmd_profile, "error profile sau khi cài reference (xem cards/after-lock-card.md)"),
    "frame-scores": (ranking.cmd_frame_scores, "bảng hỗ trợ: 1 − conf gộp sum/mean/max cho từng frame pool"),
    "lock-ranking": (lock.cmd_lock_ranking, "kiểm và khóa ranking.csv"),
    "al-eval": (ranking.cmd_al_eval, "proxy của batch đã chọn so với ngẫu nhiên và sum 1−conf không loại trùng"),
    "check-submission": (workspace.cmd_check_submission, "kiểm gói nộp đủ và đúng dạng (không chấm)"),
}


def main(argv=None):
    p = argparse.ArgumentParser(prog="lab8", description="Lab #08 — thẩm định pre-label, automation bias, active learning")
    sp = p.add_subparsers(dest="cmd", required=True)
    for name, (_, help_) in COMMANDS.items():
        s = sp.add_parser(name, help=help_)
        if name == "init":
            s.add_argument("--name"); s.add_argument("--github-user")
        if name == "install-reference":
            s.add_argument("--zip")
        if name == "profile":
            s.add_argument("--rework", action="store_true", help="so bản khóa với assisted_rework.xml")
    args = p.parse_args(argv)
    try:
        COMMANDS[args.cmd][0](args)
    except LabError as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
