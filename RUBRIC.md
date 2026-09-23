# Tiêu chí phản hồi Lab #08

**Dành cho học viên và Lab Coach.** Đây là rubric phản hồi quá trình học trên bộ frame của lab, không phải thang điểm hoặc ngưỡng đạt/trượt chính thức. GV/VinUni quyết định cách tính điểm, trọng số và hạn nộp nếu bài này được dùng để đánh giá chính thức.

Lab Coach xem **bằng chứng bạn đã áp dụng luật, kiểm tra output, giải thích sai khác và sửa lại**. Giá trị accept rate, số lỗi honeypot bắt được, shared-miss hoặc proxy active learning **không tự quyết định** mức phản hồi. Một con số thấp hoặc cao đều có thể là dữ liệu học tập hữu ích nếu bạn ghi đúng và giải thích đúng giới hạn.

## Cách đọc rubric

| Mức phản hồi | Nghĩa |
|---|---|
| **Có bằng chứng rõ** | Có file cần thiết, quyết định truy được về frame/box và luật, giải thích khớp dữ liệu, nêu giới hạn phù hợp. |
| **Cần làm rõ hoặc sửa lại** | Có làm nhưng thiếu lý do, số liệu không truy được, hoặc kết luận vượt quá điều dữ liệu cho thấy; sửa đúng phần Lab Coach chỉ ra. |
| **Chưa có bằng chứng** | Thiếu file, file không mở/kiểm được, hoặc chưa thể thấy hành động cần đánh giá. Báo Lab Coach nếu do lỗi công cụ hay hết giờ. |

Ba mức này giúp phản hồi từng tiêu chí; chúng **không quy đổi thành điểm**.

## Tiêu chí chung cho mọi học viên

| Tiêu chí | Bằng chứng cần nhìn thấy | Dấu hiệu cần làm rõ hoặc sửa lại |
|---|---|---|
| **1. Áp dụng guideline khi làm tay và thẩm định AI** | `manual_X.xml` hoặc `manual_Y.xml`, `assisted.xml`; box đúng phạm vi và class theo [guideline](cards/guideline-card.md). `decision_log.csv` có ít nhất 5 ca của bạn, ngoài 4 dòng demo `d01`, ghi frame, vật, quyết định và luật/lý do. | Bỏ qua xe để kịp giờ; giữ/xóa/sửa box mà không thể chỉ ra luật hoặc đặc điểm nhìn thấy; tự đặt luật cho ca mơ hồ thay vì ghi `escalated`. |
| **2. Giữ thứ tự làm độc lập → khóa → so reference** | `states.json`, `prediction.md`, `lock.txt` được tạo trước khi nhận gói 1; mã khóa gửi Lab Coach. Bản đã khóa giữ nguyên khi làm vòng sau. | Mở reference trước khi khóa, sửa file đã khóa, hoặc thiếu dấu vết thời điểm khóa. Nếu xảy ra lỗi, báo Lab Coach và ghi rõ. |
| **3. Đọc lỗi và giới hạn của phép đo** | `error_profile.csv`, `interpretation.md`: so dự đoán với thực tế; ba phát hiện nêu class, lát, tử số/mẫu số và hành động phù hợp. Phân biệt lỗi AI ban đầu, lỗi còn lại sau thẩm định và lỗi mới do mình tạo. | Coi accept rate là độ đúng; kết luận từ ô chỉ 1–2 xe; xem một batch nhỏ là kết luận chung về model hoặc con người. |
| **4. Rà lại và sửa có lý do** | `rework_log.csv` ghi `cause` và `action` cho từng lỗi cần xem; `assisted_rework.xml` cho thấy bản sau sửa. `reference_disputed` có lý do cụ thể là phản hồi hợp lệ. | Chỉ đổi box cho giống reference mà không ghi nguyên nhân, hoặc giữ nguyên một ca bất đồng mà không giải thích. |
| **5. Chọn frame trong ngân sách và qua bạn cặp kiểm** | `ranking.csv` đủ 50 frame; `ranking_rationale.md` giải thích điểm, cách gộp, chi phí, loại trùng/ngoại lai và top 5; `peer_check.md` ghi góp ý và quyết định sửa/giữ; `lock_ranking.txt` khóa trước gói 2. | Chỉ lấy top điểm mà không xét trùng cảnh, ngoại lai hoặc ngân sách; xem proxy `al-eval` là bằng chứng model đã học tốt hơn. |
| **6. Phản tư từ bằng chứng của mình** | `reflection.md` trả lời 4 câu trong [GUIDE](GUIDE.md#phút-220230--phản-tư-và-nộp), mỗi câu có ít nhất một số của bạn và một giới hạn của số đó. | Chép kết luận chung không gắn với bài của mình, hoặc diễn giải số gộp của lớp như kết quả cá nhân. |

## Hoàn tất và nhận phản hồi

Mọi người làm cùng một bài chính và dùng cùng tiêu chí. Mục 1–4 trong [gói nộp](README.md#gói-nộp) là bằng chứng tối thiểu cần có trước khi nhận gói 1; mục 5–8 vẫn thuộc bài chính. Nếu hết giờ, báo Lab Coach phần còn thiếu và thời điểm có thể bổ sung. [Card stretch](cards/stretch-card.md) chỉ làm sau bài chính, không thay thế tiêu chí nào ở trên.

Trước khi nộp, chạy `make check-submission` để tìm file thiếu hoặc sai dạng. Lệnh này **không đánh giá chất lượng quyết định**. Khi nhận góp ý, sửa phần chưa rõ và ghi lý do; nếu reference hoặc guideline có vẻ sai, ghi ca cụ thể để Lab Coach xem lại.
