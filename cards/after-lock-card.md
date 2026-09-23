# Card sau khi khóa — đọc `make profile`

**Mở card này ở phút 115, sau `make lock`.** Đọc trước thì phép đo của chính bạn mất nghĩa: bạn sẽ soát khác cách bạn
thật sự soát. Bài không chấm theo con số nào dưới đây.

## Phép đo là gì

Bạn đã làm hai khối trên hai tập frame cùng kiểu: một khối tay, một khối có AI. Bạn cùng nhóm làm ngược lại trên
chính hai tập đó. Lab muốn biết: **khi có AI, người thẩm định có bỏ sót theo AI không?** Nghĩa là xe model không thấy
thì người cũng không thấy, nhiều hơn so với lúc tự làm tay.

## Chỉ số

| Chỉ số | Nghĩa | Số này **không** chứng minh |
|---|---|---|
| **residual error** | Lỗi của AI mà bạn **để lọt**: còn nguyên trong bản của bạn. Đo **commission**: làm theo máy dù máy sai | |
| **new error** | Box AI **đúng** mà bạn sửa thành **sai** | |
| **shared-miss** | Trong các xe model bỏ sót: tỷ lệ bạn **cũng** bỏ sót khi có AI. So với tỷ lệ bạn bỏ sót loại xe đó khi làm tay. Đo **omission**: không hành động vì máy không báo | Kết luận thống kê: nhóm nhỏ, hai tập frame khác nhau, khối tay luôn làm trước (mệt, quen tay) |
| **honeypot** | Frame honeypot có **2** lỗi cài: 1 omission (một box đúng bị xóa) và 1 commission (một box bị đổi sang class nghe hợp lý) | Năng lực của bạn: một frame, hai lỗi |

Nghiên cứu nói gì (để so, không để tự chấm): trong một thí nghiệm 20 người thẩm định pre-label có cài lỗi, có
pre-label thì chính xác hơn và nhanh hơn, nhưng khoảng 2/3 lỗi cài vẫn lọt (Marzahl et al. 2019, arXiv:1912.00142).
Lab Coach nói thêm ở debrief.

## Đọc 6 phần `make profile` in ra

| Phần | Đọc gì |
|---|---|
| [1] Lỗi của AI | Model sai bao nhiêu xe (bỏ sót / sai class / lệch) và bịa bao nhiêu box, trên batch có AI của bạn |
| [2] Bạn sau khi thẩm định | residual, new error, và box bạn tự thêm mà không có xe |
| [3] Tay vs có AI | shared-miss khi có AI, cạnh tỷ lệ bạn bỏ sót cùng loại xe khi làm tay. Dòng cuối: tỷ lệ bỏ sót mọi xe |
| [4] Honeypot | omission và commission: bắt được hay lọt |
| [5] decision_log | tỷ lệ dòng bạn ghi `found_before_ai_toggle = yes` (tự khai) |
| [6] Dự đoán vs thực tế | 3 số trong `prediction.md` đã khóa, cạnh số thật. Chép dòng lệch nhiều nhất vào `interpretation.md` |

`submission/error_profile.csv` tách số theo class × lát (điều kiện `sunny/cloudy/rainy/night`, kích thước
`small/medium/large` theo quy ước COCO 32² / 96² px). Bỏ qua ô chỉ có 1–2 xe khi rút kết luận.

## Vòng sửa lại (phút 135–155)

`make profile` tạo `submission/rework_log.csv`: mỗi dòng là một lỗi của bạn. Với từng dòng:

1. Mở frame trong **job có AI**, tìm xe/box đó.
2. Điền `cause`, chọn một:
   `rule_unclear` (card không nói) · `missed_search` (không quét tới) · `anchored` (thấy box AI nên tin) ·
   `tool_slip` (thao tác CVAT) · `reference_disputed` (bạn cho rằng reference sai: ghi lý do vào `note`).
3. Điền `action`: bạn đã sửa gì, hoặc vì sao giữ nguyên.
4. Sửa trong CVAT, export thành `submission/assisted_rework.xml`, chạy `make rework` để xem số trước / sau.

`reference_disputed` là lựa chọn hợp lệ: nếu reference sai thật, Lab Coach sửa cho cả lớp và chạy lại số.
