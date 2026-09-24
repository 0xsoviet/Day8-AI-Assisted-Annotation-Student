# Card CVAT — thao tác dùng trong Lab #08

Phím tắt có thể khác giữa các bản CVAT: bấm **F1** trong màn gán nhãn để xem danh sách đúng với bản bạn đang dùng.

## Hai job của bạn

Máy yếu dùng **CVAT của chương trình**: Lab Coach gửi 2 link job, tên dạng `lab08-L<số thứ tự>-khoi1-tay-<X|Y>` và `lab08-L<số thứ tự>-khoi2-co-AI`. Máy bình thường dùng **CVAT local** và tạo 2 task tương đương theo hướng dẫn bên dưới. Lộ trình A/B do `init` tự xác định từ GitHub username.

| Job | Mở lúc | Có sẵn box AI? |
|---|---|---|
| Khối tay (6 frame, tập X hoặc Y) | Phút 15–45 | Không. Vẽ từ đầu |
| Khối có AI (10 frame: tập còn lại + 4 frame C) | Phút 45–95 | Có. Thẩm định từng box |

**Không mở job có AI trước khi xong khối tay.** Thấy box AI rồi mới làm tay thì phép đo bias của bạn không còn nghĩa.

## Thao tác

| Việc | Cách làm |
|---|---|
| Vẽ box | Chọn công cụ hình chữ nhật ở thanh trái, chọn label, bấm **Shape**; hoặc **N** để vẽ tiếp label vừa dùng |
| Đổi class một box | Chọn box, đổi label trong thẻ của box ở danh sách Objects bên phải |
| Xóa box | Chọn box, **Del** |
| Ẩn / hiện **mọi** box (luật quét trước) | Biểu tượng con mắt ở đầu danh sách Objects; phím **T** rồi **H** |
| Ẩn / hiện một box | Chọn box, **H** |
| Frame sau / trước | **F** / **D** |
| Hoàn tác | **Ctrl+Z** |
| Lưu | **Ctrl+S** — lưu sau mỗi frame |
| Đánh dấu frame chưa duyệt | Công cụ **Setup tag** ở thanh trái, chọn `not_reviewed`, bấm **Tag** |

## Export (phút 95–115)

1. Trong job: **Menu → Export job dataset**.
2. Định dạng **CVAT for images 1.1**. **Bỏ** ô *Save images*.
3. Tải file zip (bản CVAT mới đưa file vào trang **Requests**). Giải nén, lấy `annotations.xml`.
4. Đổi tên và chép vào `submission/`:
   - job khối tay → `manual_X.xml` (nhóm A) hoặc `manual_Y.xml` (nhóm B);
   - job khối có AI → `assisted.xml`.
5. Chạy `make states`. Lệnh báo lỗi nếu bạn export nhầm định dạng hoặc nhầm job.

Sau khi mở reference, vòng sửa lại làm **trong cùng job có AI**, rồi export lần nữa thành `submission/assisted_rework.xml`.
Không ghi đè `assisted.xml`: file đó đã khóa.

## Máy bình thường — CVAT local

Dùng CVAT chạy trên máy bạn (đã cài như Ngày 2). Nếu chưa cài hoặc máy không chạy nổi, dùng CVAT chương trình và báo Lab Coach để cấp đúng 2 job:

1. Tạo project với label dán ở tab *Raw*:
   ```json
   [{"name": "car", "type": "rectangle"}, {"name": "van", "type": "rectangle"},
    {"name": "bus", "type": "rectangle"}, {"name": "others", "type": "rectangle"},
    {"name": "not_reviewed", "type": "tag"}]
   ```
2. Task khối tay: tải 6 ảnh tập tay của bạn từ `data/frames/lab/` (nhóm A: `x01`–`x06`; nhóm B: `y01`–`y06`).
3. Task khối có AI: tải 10 ảnh (nhóm A: `y01`–`y06` + `c01`–`c04`; nhóm B: `x01`–`x06` + `c01`–`c04`), rồi
   **Actions → Upload annotations**, định dạng **CVAT 1.1**, chọn `data/cvat/prelabel_group_A.xml` hoặc `_B.xml` theo nhóm.
4. Làm và export như trên. Các lệnh `make` chạy như cũ vì chúng chỉ đọc file export.

Hai đường CVAT dùng cùng ảnh, pre-label, luật và định dạng export; việc dùng CVAT local không làm thay đổi thang chấm. Nếu CVAT đang dùng gặp sự cố, báo Lab Coach để chuyển đường còn lại, ghi thời gian ảnh hưởng vào `reflection.md`. Không chạy CVAT server trong Colab.
