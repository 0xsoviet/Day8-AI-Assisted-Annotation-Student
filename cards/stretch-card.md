# Card stretch — chỉ làm sau khi xong core

Chọn **một**. Kết quả là một đoạn ≤ 1 trang có số, ghi vào `submission/stretch.md`. Stretch không cộng thêm box phải
vẽ và không phải một đường chấm thứ hai.

## (a) Margin hay least confidence

Dùng cột `min_margin` của `make frame-scores` (hoặc tự tính `p_top1 − p_top2`). Xếp 50 frame theo margin nhỏ nhất và
theo `1 − conf`. Top-10 hai cách trùng bao nhiêu frame? Đổi cách gộp box (tổng / max) thì sao? Frame nào chỉ lên top
theo margin, và nhìn trên contact sheet nó có gì?

## (b) Loại trùng tự động

So loại trùng bằng mắt (contact sheet + `seq_id`, `time_s`) với loại trùng tự động: perceptual hash, hoặc FiftyOne
`compute_uniqueness` (cần Python ≥ 3.10 và cài thêm thư viện; thời gian chạy trên 50 ảnh chưa đo). Hai cách bất đồng ở
frame nào?

## (c) Quét ngưỡng conf trên pre-label

Pre-label dùng ngưỡng 0,40. `data/pool/pool_predictions.csv` có mọi box conf ≥ 0,25 trên pool. Sau khi cài gói 2, so
số box ở các ngưỡng 0,25 / 0,40 / 0,60 trên vài frame bạn đã nhìn: hạ ngưỡng thêm được xe thật hay thêm box bịa?

## (d) Confound thứ tự

Trong bài này khối tay luôn làm trước khối có AI. Chỉ ra con số nào của bạn có thể bị thứ tự này làm lệch (mệt,
quen tay, quen cảnh) và theo hướng nào. Đề xuất một thiết kế Latin square cho lớp 30 người: ai làm gì trước, cần bao
nhiêu tập frame, và cái giá phải trả.
