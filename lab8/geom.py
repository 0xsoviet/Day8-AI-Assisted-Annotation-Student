"""Hình học box và các ngưỡng dùng chung. Mọi định nghĩa đo của lab nằm ở lab-design §5.2; file này chỉ giữ số."""

MATCH_IOU = 0.5      # ghép đúng với reference (quy ước lớp học, không phải ngưỡng chất lượng)
LOC_IOU = 0.3        # 0,3–0,5 với reference = lỗi lệch vị trí; cũng là ngưỡng ghép cặp khi tính 4 trạng thái
ACCEPT_IOU = 0.99    # "giữ nguyên" so với pre-label
LOOSE_IOU = 0.75     # đã ghép đúng nhưng box lỏng (chỉ để thông tin, không tính lỗi)
SMALL, MEDIUM = 32 * 32, 96 * 96   # quy ước kích thước mượn của COCO, không phải chuẩn dự án
CLASSES = ("car", "van", "bus", "others")


def iou(a, b):
    ix = max(0.0, min(a["x2"], b["x2"]) - max(a["x1"], b["x1"]))
    iy = max(0.0, min(a["y2"], b["y2"]) - max(a["y1"], b["y1"]))
    inter = ix * iy
    union = area(a) + area(b) - inter
    return inter / union if union > 0 else 0.0


def area(b):
    return max(0.0, b["x2"] - b["x1"]) * max(0.0, b["y2"] - b["y1"])


def size_bucket(b):
    a = area(b)
    return "small" if a < SMALL else "medium" if a < MEDIUM else "large"
