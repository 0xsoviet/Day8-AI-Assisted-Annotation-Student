"""Đọc/ghi file "CVAT for images 1.1". Chỉ lấy box chữ nhật và tag frame; bỏ polygon/point nếu có."""
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

NOT_REVIEWED = "not_reviewed"


def frame_id(name):
    """`assisted/c01.jpg` -> `c01`: CVAT giữ đường dẫn con nếu ảnh được tải lên từ thư mục."""
    return os.path.splitext(os.path.basename(name))[0]


def read(path):
    """Trả về {frame_id: {"boxes": [...], "tags": set(), "size": (w, h)}}."""
    root = ET.parse(path).getroot()
    out = {}
    for im in root.iter("image"):
        fid = frame_id(im.get("name", ""))
        if fid in out:
            raise ValueError(f"{path}: frame {fid} xuất hiện hai lần")
        boxes = []
        for b in im.iter("box"):
            if b.get("outside") == "1":
                continue
            boxes.append(dict(cls=b.get("label"), source=b.get("source", ""),
                              x1=float(b.get("xtl")), y1=float(b.get("ytl")),
                              x2=float(b.get("xbr")), y2=float(b.get("ybr"))))
        tags = {t.get("label") for t in im.iter("tag")}
        out[fid] = dict(boxes=boxes, tags=tags, size=(int(float(im.get("width", 0))), int(float(im.get("height", 0)))))
    if not out:
        raise ValueError(f"{path}: không có thẻ <image>. Cần export định dạng 'CVAT for images 1.1', không phải 'CVAT for video'.")
    return out


def write(path, frames, sizes):
    """frames: [(file_name, [box...])] theo đúng thứ tự ảnh trong job (CVAT sắp theo tên)."""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<annotations>", "  <version>1.1</version>"]
    for i, (name, boxes) in enumerate(frames):
        w, h = sizes[name]
        lines.append(f'  <image id="{i}" name={quoteattr(name)} width="{w}" height="{h}">')
        for b in boxes:
            lines.append(f'    <box label={quoteattr(b["cls"])} source="auto" occluded="0" xtl="{b["x1"]:.1f}" '
                         f'ytl="{b["y1"]:.1f}" xbr="{b["x2"]:.1f}" ybr="{b["y2"]:.1f}" z_order="0"></box>')
        lines.append("  </image>")
    lines.append("</annotations>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
