"""Gán lộ trình và kịch bản ổn định từ tài khoản GitHub của học viên."""
import hashlib
import re

from .data import LabError


def normalize_user(value):
    user = (value or "").strip().lstrip("@").lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?", user):
        raise LabError("GitHub username không hợp lệ; nhập tên tài khoản, không nhập URL hoặc email.")
    return user


def assignment_for(value):
    """Cùng một username luôn cho cùng một trong bốn tổ hợp A/B × S1/S2."""
    user = normalize_user(value)
    slot = hashlib.sha256(f"lab8-assignment-v1:{user}".encode()).digest()[0] % 4
    return (("A", "S1"), ("A", "S2"), ("B", "S1"), ("B", "S2"))[slot]
