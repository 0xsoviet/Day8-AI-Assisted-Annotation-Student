# Card guideline — Lab #08

Một trang luật dùng cho cả khối làm tay lẫn khối có AI. Trích mục của card này khi ghi `decision_log.csv`
(vd "Card mục Schema"). Card không nói tới trường hợp nào thì **không tự đặt luật**: ghi `escalated` và hỏi Lab Coach.

## Schema

| Class | Gồm | Không gồm | Ghi chú |
|---|---|---|---|
| `car` | Xe con: sedan, hatchback, taxi, SUV | | |
| `van` | Xe thân hộp mui cao liền khối, đầu xe ngắn: minivan, xe 7–16 chỗ, van chở hàng | | Model COCO **không có** class van → nó sẽ gọi van là `car` hoặc `others`. Đây là lỗi có quy luật, không phải ngẫu nhiên |
| `bus` | Xe buýt, xe khách cỡ lớn | | Hay nhầm với `others` |
| `others` | Xe tải, xe bồn, xe chuyên dụng | | Model gọi là `truck`, đã đổi tên sang `others` |
| — | | Người, xe đạp, xe máy | Ngoài schema của bài này: không vẽ. Nếu gặp box như vậy, xóa và ghi `out-of-schema` |

Tag frame: `not_reviewed` — gắn cho frame bạn **chưa kịp duyệt**. Frame có tag này không được tính là accepted.

Xem cặp đối chiếu van / car ở [img/contrast_van_vs_car.jpg](img/contrast_van_vs_car.jpg): hai xe cùng màu, cùng hướng,
khác nhau ở **dáng thân** (thân hộp, mui cao) chứ không phải kích thước.

## Vẽ box

- Vẽ mọi xe trong schema mà bạn thấy **khoảng một nửa thân trở lên**. Không có kích thước tối thiểu: xe nhỏ ở xa
  vẫn vẽ nếu nhận ra là xe.
- Box ôm sát thân xe, không tính bóng đổ trên mặt đường.
- Xe bị **mép ảnh** cắt: box dừng ở mép ảnh.
- Xe bị **xe khác che** một phần: box ôm cả phần bị che theo đường bao bạn hình dung được (quy ước của bộ dữ liệu gốc).
  Không hình dung được thì vẽ phần thấy và ghi `escalated`.
- Mỗi xe **một** box. Hai box trên cùng một xe → xóa box sai.
- Script ghép box với reference ở IoU ≥ 0,5 và cùng class. Lệch vài pixel không sao; box lỏng gấp rưỡi xe thì bị tính là lệch.

## Vùng xám và vật khó thấy

- Vùng tô xám là vùng không gán nhãn. Xe có **tâm** nằm trong vùng xám: không vẽ.
- Xe thấy **ít hơn khoảng một nửa** (bị xe khác, vùng xám hoặc mép ảnh che): vẽ hay không đều **không bị tính** đúng/sai.
  Đừng mất thời gian vào chúng.

## Quét trước

Luật slide 22, áp dụng cho khối có AI: **quét ảnh gốc trước khi bật lớp AI**.

1. Mở frame, ẩn toàn bộ box AI (xem [cvat-card.md](cvat-card.md)).
2. Quét ảnh theo một đường cố định (vd trái → phải, gần → xa), đếm và nhớ những xe dễ bị bỏ sót: xe nhỏ ở xa, xe tối,
   xe bị che, xe sát mép.
3. Bật lại box AI. Kiểm xem xe bạn vừa đếm có box chưa, rồi mới soát từng box AI.

Vì sao có luật này — **bẫy hợp lý**: khi box AI trông hợp lý, người soát thường dừng tìm lỗi, dù box đó chưa chắc đúng
và xe không có box thì không có gì để nhìn vào. Gặp cảm giác "trông ổn rồi" thì đó là lúc bẫy này hoạt động.

Khi ghi `decision_log.csv`, cột `found_before_ai_toggle` = `yes` nếu bạn thấy vật/lỗi đó **trong bước 2**, trước khi bật box AI.

## Khi nào `escalated`

Ghi một dòng `decision_log.csv` với `state = escalated` và hỏi Lab Coach khi:

- không rõ box bao phần bị che hay chỉ phần thấy;
- xe nằm một phần trong vùng xám và bạn không chắc tâm ở đâu;
- van / car mơ hồ (SUV cao, xe bán tải có thùng kín);
- xe cắt mép mà không chắc đã thấy đủ một nửa;
- frame quá tối không phân biệt được class.

Luật mới chỉ do Lab Coach đặt, và Lab Coach báo cho cả lớp cùng lúc.
