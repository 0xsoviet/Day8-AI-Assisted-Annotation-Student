# Hướng dẫn từng khối — Lab #08

Mở file này cạnh CVAT. Cả hai loại máy dùng [notebook Colab](notebooks/day8-colab.ipynb) để chạy AI và các lệnh phân tích. Các lệnh `make` dưới đây là tên bước tương ứng trong notebook; nếu chạy tại repo trên máy, gõ `python -m lab8 <lệnh>` khi không có `make`.

## Phút 0–15 — Nhận việc và làm mẫu

1. Tạo repo private riêng từ template, tải ZIP repo rồi mở notebook Colab. Điền tên và GitHub username; notebook tự xác định A/B và S1/S2. Không đổi username giữa buổi.
2. Trên Colab chạy `verify-data` và `init`; nếu chạy tại repo trên máy:
   ```bash
   make verify-data
   make init NAME="Họ Tên" GITHUB_USER=tai-khoan-github
   ```
   `init` tạo `submission/` với file mẫu. Chạy lại không xóa bài đang làm.
3. Chạy YOLO trong notebook trên frame demo `d01` ở hai ngưỡng confidence; ghi một thay đổi và một giới hạn của AI. Đọc [card guideline](cards/guideline-card.md) và [card 4 trạng thái](cards/four-states-card.md).
4. Máy bình thường tạo hai task trên CVAT local; máy yếu nhận hai link job trên CVAT chương trình. Xem [card CVAT](cards/cvat-card.md). Chỉ mở khối có AI sau khi đã xong khối tay.

**Xong khi:** mở được khối tay, biết lộ trình và chi phí, có `submission/ai_probe.json`; `decision_log.csv` có 4 dòng mẫu `d01`.

Từ ngữ lạ: [thẻ từ vựng](cards/vocabulary-card.md).

## Phút 15–45 — Khối 1: làm tay

Job `...-khoi1-tay-...`, 6 frame, **không có box sẵn**. Vẽ mọi xe theo card guideline.

- Ghi giờ bắt đầu và giờ xong (một dòng trong `reflection.md` sau này dùng tới).
- Lưu (**Ctrl+S**) sau mỗi frame.
- Không mở job có AI trong lúc này.

**Checkpoint phút 30:** xong ≥ 3 frame. Chậm hơn thì báo Lab Coach, đừng bỏ qua xe để kịp.

## Phút 45–95 — Khối 2: thẩm định pre-label

Job `...-khoi2-co-AI`, 10 frame, **có box AI sẵn**. Batch này có **một frame honeypot** (Lab Coach đã cài lỗi vào đó).
Bạn không biết là frame nào.

Với **mỗi** frame, theo luật [Quét trước](cards/guideline-card.md#quét-trước):

1. Ẩn mọi box AI.
2. Quét ảnh gốc theo một đường cố định, đếm xe dễ bị sót (nhỏ, xa, tối, bị che, sát mép).
3. Bật lại box AI. Xe bạn vừa đếm đã có box chưa? Rồi mới soát từng box: đúng xe, đúng class, ôm vừa?
4. Sửa: giữ nguyên / kéo lại hoặc đổi class / xóa / vẽ thêm.

Ghi **ít nhất 5 dòng** vào `submission/decision_log.csv` cho những ca đáng chú ý (không tính 4 dòng mẫu):

| Cột | Ghi gì |
|---|---|
| `frame_id` | vd `y03` (tên ảnh trong CVAT) |
| `object` | mô tả đủ để tìm lại: màu, vị trí, `x ≈ …` |
| `state` | `accepted` / `edited` / `deleted` / `added` / `escalated` / `not_reviewed` / `out-of-schema` |
| `rule_or_reason` | trích mục card, vd "Card mục Vẽ box: …". Hai ca giống nhau mà xử lý khác: ghi **một đặc điểm nhìn thấy** làm chúng khác |
| `found_before_ai_toggle` | `yes` nếu bạn thấy vật/lỗi này ở bước 2, trước khi bật box AI; `no` nếu không |
| `signed_by` | tên bạn |

Ca card không nói tới: ghi `escalated` và hỏi Lab Coach. Không tự đặt luật.

**Checkpoint phút 70:** xong 6 frame đầu của job (tập X hoặc Y). Hết giờ mà còn frame chưa duyệt: gắn tag
`not_reviewed` cho frame đó ([card CVAT](cards/cvat-card.md)). Frame có tag này **không** bị tính là accepted; frame
không có tag thì mọi box AI còn lại đều được tính là bạn đã chấp nhận.

## Phút 95–105 — Nghỉ

Đã xong thì export trước khi nghỉ.

## Phút 105–115 — Export, dự đoán, khóa bài

1. Export 2 job theo [card CVAT](cards/cvat-card.md#export-phút-95115): `submission/manual_X.xml` (nhóm A) hoặc
   `submission/manual_Y.xml` (nhóm B), và `submission/assisted.xml`.
2. `make states` → 4 trạng thái của bạn, tách theo class và lát.
3. Điền 3 số vào `submission/prediction.md`: bạn đoán accept rate của mình, số lỗi honeypot bạn đã sửa được, số xe
   bạn còn bỏ sót trong batch có AI. Đoán lệch là bình thường; bạn sẽ phân tích độ lệch đó.
4. `make lock` → in một mã 12 ký tự. Gửi mã cho Lab Coach.

Sau `make lock`, các file `manual_*.xml`, `assisted.xml`, `decision_log.csv`, `prediction.md`, `states.json`
**không sửa nữa**: mọi lệnh sau kiểm lại mã khóa và báo lỗi nếu file đổi.

**Xong khi:** Lab Coach nhận mã của bạn. Lab Coach phát **gói 1** (reference).

## Phút 115–135 — Đọc lỗi của AI và của mình

1. `make install-reference ZIP=<đường dẫn gói 1>`
2. Mở [card sau khi khóa](cards/after-lock-card.md). Lab Coach giải thích phép đo trong 2 phút.
3. `make profile` → bảng số và `submission/error_profile.csv`, `submission/rework_log.csv`, `submission/reflection.md`.
4. Viết `submission/interpretation.md`:
   - một dòng: số nào bạn đoán lệch nhiều nhất, lệch bao nhiêu, theo hướng nào;
   - 3 phát hiện, mỗi phát hiện đủ **class + lát + tử số/mẫu số + loại hành động**
     (sửa guideline · luyện tập tập trung · thêm bước kiểm). Bỏ ô chỉ có 1–2 xe.

## Phút 135–155 — Rà lỗi và sửa lại

Làm theo mục "Vòng sửa lại" của [card sau khi khóa](cards/after-lock-card.md#vòng-sửa-lại-phút-135155):
điền `cause` và `action` cho từng dòng `rework_log.csv`, sửa trong job có AI, export thành
`submission/assisted_rework.xml`, rồi `make rework`. Không có gì để sửa: chép `assisted.xml` thành `assisted_rework.xml`.

**Một ca bất đồng, làm cá nhân hoặc cùng bạn:** chọn một frame chung `c01`–`c04`, điền `case_review.md`.
Làm cá nhân: so quyết định của chính mình trong bản đã khóa với reference gói 1. Làm cùng bạn: sau khi **cả hai đã khóa**,
trích quyết định từ hai bản khóa để so, rồi dùng reference làm căn cứ kết luận. Cả hai cách đều cần frame/vật, quyết định ban đầu, góc nhìn thứ
hai, bằng chứng từ guideline và quyết định sửa/giữ. Chọn cách xử lý một frame tương tự sau này: kiểm nhanh hay vẽ
lại; nói cần bằng chứng gì trước khi cân nhắc tự chấp nhận nhãn. Đây là giả định học tập, không có nhãn nào được tự
chấp nhận trong bài. Đồng ý nhau không tự chứng minh là đúng; nếu reference có vẻ sai, ghi `reference_disputed` với
frame/vật/lý do.

## Phút 155–165 — Nghỉ

## Phút 165–195 — Phần (c): xếp hạng 50 frame

Đọc [card pool](cards/pool-card.md) và [cost card](cards/cost-card.md) (kịch bản của bạn ghi trong `submission/info.json`).

1. Scoring từng box: `1 − conf`.
2. Gộp theo frame: `sum` / `mean` / `max`, chọn theo kịch bản chi phí. `make frame-scores` tính sẵn cả ba và
   tạo `ai_priority` / `ai_suggested` theo `sum(1−conf)`. Xem top 5 gợi ý, nêu ít nhất một frame bạn giữ hoặc đổi và
   lý do. Lệnh điền bản nháp 50 rank nếu `ranking.csv` còn trống; không ghi đè bản bạn đã sửa. Gợi ý chưa thấy vật
   model bỏ sót, chưa loại trùng hay ngoại lai.
3. Sampling: loại trùng (`seq_id` + `time_s`, contact sheet), gắn cờ ngoại lai.
4. Điền `submission/ranking.csv` (50 dòng) và `submission/ranking_rationale.md` (lý do + giải thích top 5 + một câu cold start).

**Checkpoint phút 180:** mọi frame đã có `frame_score`.

## Phút 195–205 — Tự kiểm hoặc cùng bạn kiểm, khóa xếp hạng

1. **Làm cá nhân:** tạm ẩn rank của mình, xem lại top-10 bằng contact sheet và `pool_frames.csv`; so với gợi ý
   `ai_suggested`. **Làm cùng bạn:** sau khi mỗi người đã xếp độc lập, đổi top-10; người kia tìm frame trùng cảnh,
   ngoại lai, thiếu đa dạng hoặc lý do không khớp chi phí. Có thể khác kịch bản; khi so phải ghi rõ chi phí của từng
   người, không bắt buộc ghép S1 ↔ S2.
2. Sửa `ranking.csv` nếu cần; ghi vào `submission/peer_check.md` góc nhìn thứ hai, bằng chứng và quyết định sửa/giữ.
   Đây là cùng một yêu cầu bằng chứng cho hai cách làm; điểm không phụ thuộc việc có bạn cặp.
3. `make lock-ranking` → gửi mã cho Lab Coach. Lab Coach phát **gói 2**.
4. `make install-reference ZIP=<đường dẫn gói 2>`, rồi `make al-eval`.

## Phút 205–220 — Quyết định lượt sau và debrief cả lớp

Đọc `al_eval.json`. Điền `next_round.md`: một tín hiệu đã thấy, ba frame pool **chưa chọn** cho lượt sau, vì sao chúng
bổ trợ nhau, và một quy tắc chọn mẫu sẽ đổi. Đây là **kế hoạch vòng hai**, chưa có nhãn mới hay model huấn luyện lại.
Sau đó Lab Coach chiếu số gộp của cả lớp, không gắn tên. Luật: không hỏi bạn khác ra số nào. Ghi một câu cho mình:
"lớp thường …, mình …, vì …", có số.

## Phút 220–230 — Phản tư và nộp

1. Trả lời 4 câu trong `submission/reflection.md`. Mỗi câu có ≥ 1 số của bạn và một câu "số này không chứng minh …".
2. `make check-submission` → báo thiếu gì. Lệnh này **không** chấm điểm.
3. Đối chiếu [rubric 100 điểm](RUBRIC.md). Từ Colab tải `submission.zip`, giải nén vào repo private riêng trên máy, kiểm tra rồi push lên GitHub để hệ thống chấm.

## Phút 230–240 — Dự phòng

Hoàn tất phần còn thiếu. Xong sớm: chọn một bài trong [card stretch](cards/stretch-card.md).

## Khi gặp lỗi

| Gặp | Làm |
|---|---|
| CVAT không vào được | Báo Lab Coach ngay để được cấp đường CVAT còn lại; xem [card CVAT](cards/cvat-card.md) |
| `make states` báo sai định dạng / sai job | Export lại đúng **CVAT for images 1.1**, đúng job, đổi tên đúng như card CVAT |
| `make verify-data` báo khác sha256 | Không sửa `data/`. Tải lại repo |
| Lỡ mở job có AI trước khi xong khối tay | Báo Lab Coach và ghi vào `reflection.md`. Đừng giấu: số của bạn vẫn dùng được nếu Lab Coach biết |
| Lỡ sửa file sau khi khóa | Lệnh sẽ báo mã khóa không khớp. Báo Lab Coach; đừng khóa lại |
| Hết giờ | Mục 1–4 của gói nộp là tối thiểu. Mục 5–8 thiếu thì báo Lab Coach, nộp bổ sung theo hạn Lab Coach thông báo |
