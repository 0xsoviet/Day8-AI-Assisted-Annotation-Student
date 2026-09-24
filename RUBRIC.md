# Rubric Lab #08 — 100 điểm

**Dành cho học viên.** Đây là thang 100 điểm mô tả bằng chứng và lập luận trong [gói nộp](README.md#gói-nộp). Sau khi bạn nộp bài, **hệ thống chấm bài** theo rubric được cấu hình; Lab Coach không chấm tay hay tự điều chỉnh điểm. Rubric này không đặt ngưỡng đạt/trượt của chương trình; hạn nộp và quy tắc nộp muộn theo thông báo của GV/VinUni.

Điểm **không tăng hoặc giảm theo độ lớn** của accept rate, shared-miss, residual error, số lỗi honeypot bắt được, hay proxy active learning. Các số ấy là dữ liệu để bạn phân tích. Một số thấp hoặc cao vẫn có thể đạt điểm phần phân tích nếu được tính đúng, giải thích đúng và nêu đúng giới hạn. [Card stretch](cards/stretch-card.md) là tùy chọn, không cộng điểm và không thay thế bài chính.

Notebook Colab cho bạn chạy YOLO thật trên frame demo và lưu `ai_probe.json`. Bảng `frame_scores.csv` cho thấy gợi ý chọn pool từ dự đoán model. Bài nộp và thang điểm dưới đây vẫn tổng **100 điểm**; không có điểm thưởng vì có bạn cặp hay vì chọn được nhiều lỗi hơn.

## Bảng chấm

| Tiêu chí | Bằng chứng và cách phân điểm | Điểm tối đa |
|---|---|---:|
| **1. Gán nhãn và thẩm định theo guideline** | `manual_X.xml` hoặc `manual_Y.xml` và `assisted.xml` mở được, đúng tập frame; frame chưa kịp duyệt được gắn `not_reviewed` đúng cách: **8**. Box đã duyệt đúng phạm vi, class và quy tắc trong [guideline](cards/guideline-card.md); ca mơ hồ được ghi `escalated` thay vì tự đặt luật: **10**. `decision_log.csv` có ít nhất 5 ca của bạn ngoài 4 dòng demo, mỗi ca truy được frame/vật, quyết định và lý do theo luật: **7**. | **25** |
| **2. Bằng chứng làm độc lập và khóa trước khi xem reference** | `states.json` và `prediction.md` có đủ nội dung, dự đoán ghi trước khi mở đáp án: **4**. `lock.txt` hợp lệ, mã đã gửi Lab Coach trước gói 1; bản khóa giữ nguyên: **6**. | **10** |
| **3. Phân tích lỗi và giới hạn phép đo** | `error_profile.csv` và `interpretation.md` phân biệt lỗi AI ban đầu, lỗi còn lại sau thẩm định và lỗi mới; so dự đoán với thực tế: **6**. Ba phát hiện có class, lát, tử số/mẫu số và hành động phù hợp: **9**. Nêu giới hạn của batch nhỏ, ô ít vật và từng chỉ số; không coi accept rate là độ đúng: **5**. | **20** |
| **4. Rà lỗi và sửa lại có lý do** | `rework_log.csv` ghi `cause`, `action` và lý do truy được cho từng lỗi cần xem; `reference_disputed` có lý do cụ thể nếu có tranh luận: **7**. `assisted_rework.xml` mở được và thể hiện bản sau sửa; trường hợp không có lỗi cần sửa, giữ bản export và ghi rõ lý do: **6**. `case_review.md` đối chiếu một ca frame C bằng quyết định độc lập, góc nhìn thứ hai, guideline, kết luận sửa/giữ và cách chuyển ca tương tự tới kiểm nhanh/vẽ lại: **2**. Góc nhìn thứ hai có thể là reference khi làm cá nhân hoặc quyết định độc lập của bạn học khi làm cùng bạn; tiêu chí như nhau. | **15** |
| **5. Xếp hạng frame theo ngân sách** | `ranking.csv` đủ 50 frame, thứ tự và chi phí không vượt ngân sách: **5**. Điểm box/frame, cách gộp `sum`/`mean`/`max` và lựa chọn theo kịch bản chi phí được giải thích: **4**. `ranking_rationale.md` giải thích top 5, loại trùng, ngoại lai và ít nhất một quyết định giữ/đổi gợi ý model bằng ảnh/dữ liệu: **5**. `peer_check.md` ghi kết quả tự kiểm hoặc bạn kiểm cùng quyết định sửa/giữ; `lock_ranking.txt` có trước gói 2: **3**. `next_round.md` dùng phản hồi để đề xuất ba frame chưa chọn, giải thích cách bổ trợ nhau và giới hạn chưa huấn luyện lại: **3**. | **20** |
| **6. Phản tư dựa trên bài của mình** | `reflection.md` trả lời đủ 4 câu trong [GUIDE](GUIDE.md), mỗi câu có số của chính bạn và lập luận gắn với bài: **8**. Nêu điều những số đó chưa chứng minh, không suy kết quả cá nhân từ số gộp của lớp: **2**. | **10** |
| **Tổng** | | **100** |

## Nộp bài và nhận kết quả chấm

Các điểm trong bảng là **điểm tối đa** cho từng phần bằng chứng. Hệ thống chấm và trả kết quả sau khi nhận bài; file thiếu, sai dạng hoặc không mở được được xử lý theo quy tắc của hệ thống. Lab Coach hỗ trợ khi có sự cố CVAT hoặc cần dùng [đường dự phòng](cards/cvat-card.md); việc xử lý ngoại lệ của bài nộp phải theo quy trình của hệ thống, không phải quyết định cho điểm của Lab Coach.

Mục 1–4 trong [gói nộp](README.md#gói-nộp) là bằng chứng tối thiểu để khóa và nhận gói 1; mục 5–8 vẫn là bài chính và có điểm trong thang 100. Hết giờ hoặc cần nộp bổ sung thì báo Lab Coach; thời hạn và cách xử lý điểm nộp muộn theo thông báo của GV/VinUni.

Trước khi nộp, chạy `make check-submission` để tìm file thiếu hoặc sai dạng. Lệnh này **chỉ kiểm tra trên máy bạn, không phải hệ thống chấm bài**. Nếu bạn cho rằng reference hoặc guideline sai, ghi frame/vật/lý do để Lab Coach kiểm tra và chuyển ca cần xử lý theo quy trình; Lab Coach không sửa điểm trực tiếp.
