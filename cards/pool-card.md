# Card dữ liệu pool — phần (c) xếp hạng 50 frame

Bạn có 50 frame chưa gán nhãn (`p001`–`p050`) và dự đoán của model trên từng frame. Việc của bạn: xếp hạng 50 frame
theo thứ tự nên gửi đi gán nhãn, và chọn một batch vừa ngân sách ([cost card](cost-card.md)). Dự đoán pool đã được đóng băng để mọi người có cùng đầu vào; bạn chạy AI thật trên frame demo `d01` ở Colab.

## Ba file

| File | Một dòng là | Cột bạn dùng |
|---|---|---|
| `data/pool/pool_frames.csv` | một frame | `seq_id` (mã video), `camera_id` (mã địa điểm quay), `time_s` (giây tính từ đầu đoạn cắt của video đó) |
| `data/pool/pool_predictions.csv` | một box model thấy, conf ≥ 0,25 | `frame_id`, `box_id`, `x1,y1,x2,y2`, `pred_class`, `conf`, `p_top1`, `class_2`, `p_top2` |
| `data/pool/pool_contact_sheet.jpg` | 50 ảnh thu nhỏ có ghi `frame_id` | nhìn để loại trùng và tìm frame ngoại lai |

- `conf` = `p_top1` = điểm class cao nhất của box. `class_2` / `p_top2` = class có điểm cao thứ hai và điểm của nó.
- Điểm class là sigmoid **độc lập từng lớp**: `p_top1 + p_top2` không cộng thành 1, và chúng không phải xác suất đúng.
- Ngưỡng 0,25 ở đây thấp hơn ngưỡng 0,40 của pre-label, nên pool có cả những box model rất không chắc.

## Bốn bước, tách rõ

1. **Scoring từng box**: least confidence `1 − conf`. Điểm này chỉ đo model phân vân về **class**; box lệch vị trí
   hoặc xe model không thấy thì không có điểm nào.
2. **Gộp theo frame**: `sum`, `mean` hoặc `max`. Chọn theo kịch bản chi phí của bạn và ghi vì sao vào
   `ranking_rationale.md`. `make frame-scores` tính sẵn cả ba vào `submission/frame_scores.csv`. Cột `ai_priority`
   là thứ tự theo `sum(1−conf)`; `ai_suggested=1` là đề xuất cơ sở vừa ngân sách. Đề xuất này **chưa** xét ảnh trùng,
   ngoại lai, độ đa dạng hoặc vật model bỏ sót. Nếu `ranking.csv` còn trống, lệnh điền bản nháp đủ 50 rank theo
   gợi ý; chạy lại **không ghi đè** quyết định bạn đã sửa. Xem top 5 gợi ý, nêu ít nhất một quyết định giữ/đổi có
   bằng chứng. Nếu bạn chọn `mean` hoặc `max`, cập nhật cột `frame_score` và thứ tự tương ứng.
3. **Sampling**: trước khi lấy top theo ngân sách,
   - loại trùng: cùng `seq_id` và `time_s` cách nhau rất gần (vài phần mười giây) là gần như cùng một cảnh. Tự chọn
     ngưỡng khoảng cách và ghi lại. Cùng `camera_id` khác `seq_id` là cùng địa điểm, khác lúc quay: không tự động là trùng;
   - gắn cờ ngoại lai vô ích: frame điểm cao nhưng gán nhãn cũng không dạy được gì (lóa, xe chỉ còn vài pixel). Kiểm bằng
     contact sheet, đừng chỉ nhìn số.
4. **Xếp hạng 50 frame** và giải thích 5 frame đầu trong `ranking_rationale.md`.

Nếu một frame không có box, `sum_lc=0` **không chứng minh** ảnh không có xe; model có thể bỏ sót toàn bộ. Nhìn contact sheet và ảnh gốc trước khi quyết định.

## Điền `submission/ranking.csv`

`make init` đã tạo sẵn 50 dòng. Mỗi frame đúng một dòng:

| Cột | Giá trị |
|---|---|
| `rank` | 1…50, không trùng. 1 = gửi gán nhãn trước nhất |
| `frame_score` | điểm frame của bạn sau khi gộp |
| `selected` | `1` nếu frame nằm trong batch gửi đi, `0` nếu không. Tổng chi phí các frame `1` ≤ ngân sách |
| `flag` | `ok`, `duplicate` (trùng cảnh với frame xếp trên) hoặc `outlier` (ngoại lai vô ích) |
| `reason` | ngắn; bắt buộc với frame bạn gắn `duplicate` / `outlier` hoặc xếp trái với điểm |

Frame gắn `duplicate` hay `outlier` vẫn có `rank`; thường bạn xếp chúng xuống dưới và để `selected = 0`.

Sửa bằng bảng tính hay trình soạn thảo đều được; giữ dấu phẩy làm dấu phân cách và mã hóa UTF-8. `make lock-ranking` báo lỗi nếu
thiếu frame, trùng rank, sai `flag` hoặc vượt ngân sách.

## Sau khi khóa

`make al-eval` (cần gói 2 Lab Coach phát) so batch của bạn với 1.000 lần chọn ngẫu nhiên, với cách `sum` không loại
trùng, và với chính điểm của bạn khi bỏ bước sampling. Đọc dòng giới hạn nó in ra cuối cùng: proxy này **không** đo model
sau khi học có tốt hơn không.

Sau đó điền `next_round.md`: dùng ít nhất một tín hiệu từ `al_eval.json` hoặc `error_profile.csv`, chọn **3 frame chưa
chọn** cho lượt giả định tiếp theo, giải thích cách chúng bổ trợ nhau và một quy tắc scoring/sampling bạn sẽ đổi.
Không gán nhãn, huấn luyện lại hay tuyên bố model đã tốt hơn ở lượt này.
