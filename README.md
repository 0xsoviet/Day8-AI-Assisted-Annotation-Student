# Day 8 — Thẩm định pre-label và xếp hạng active learning

**Dành cho học viên · 240 phút trên lớp · làm cá nhân.** Tạo repo **private** của bạn từ template này, làm bài trong
đó, push kết quả rồi nộp link repo theo cách Lab Coach thông báo.

Pre-label đổi việc gán nhãn từ **vẽ nhãn** sang **thẩm định nhãn máy vẽ**. Hôm nay bạn làm cả hai trên cùng kiểu cảnh
giao thông, rồi đo xem cách làm của mình thay đổi ra sao. Sau đó bạn chọn frame nên gửi đi gán nhãn tiếp khi ngân sách
có hạn.

Bạn sẽ:

1. **Làm tay** 6 frame: vẽ box mọi xe theo card guideline.
2. **Thẩm định pre-label** 10 frame do một model thật gợi ý: giữ, sửa, xóa hoặc vẽ thêm từng box. Batch này có một frame
   honeypot đã cài lỗi.
3. **Khóa bài**, rồi mới xem reference và đọc lỗi của AI và của chính mình theo class, điều kiện, kích thước.
4. **Sửa lại** lỗi của mình, ghi nguyên nhân từng lỗi.
5. **Xếp hạng 50 frame** chưa gán nhãn theo thứ tự nên gửi đi gán nhãn, trong một ngân sách cố định.

Bài **không** chấm theo độ lớn của các con số bạn đo được. Bài xét bằng chứng và lập luận: bạn làm gì, vì sao, và con số
nào không chứng minh điều gì. Làm đúng như bình thường bạn vẫn làm; con số thật có ích hơn con số đẹp.

## Bắt đầu trong 5 phút

Cần: Python ≥ 3.8 (không cài thêm thư viện), trình duyệt mở được CVAT của lớp.

1. Trên trang repo này bấm **Use this template → Create a new repository**, chủ sở hữu là tài khoản của bạn, chọn
   **Private**. Vào repo mới: **Settings → Collaborators → Add people**, thêm tài khoản GitHub Lab Coach thông báo
   (không thêm thì Lab Coach không xem được bài). Clone repo của bạn về máy, mở terminal trong thư mục repo.
   Mở link repo mà GitHub báo 404: tài khoản của bạn chưa được cấp quyền đọc (hoặc bạn chưa nhận lời mời trong email)
   — báo Lab Coach.
2. Chạy:
   ```bash
   make verify-data
   make init NAME="Họ Tên" GROUP=A SCENARIO=S1
   ```
   Lab Coach phát **nhóm** (A/B) và **kịch bản chi phí** (S1/S2). Máy không có `make` (thường là Windows): thay `make <lệnh>`
   bằng `python -m lab8 <lệnh>`, vd `python -m lab8 init --name "Họ Tên" --group A --scenario S1`. `make help` liệt kê
   mọi lệnh.
3. Mở [GUIDE.md](GUIDE.md) cạnh CVAT và làm theo từng khối thời gian.

## Lịch 240 phút

| Phút | Việc | Kết quả |
|---:|---|---|
| 0–15 | Nhận việc, xem frame demo 4 trạng thái | `make init` xong, mở được 2 job CVAT |
| 15–45 | Khối 1: làm tay 6 frame | Job làm tay đã lưu |
| 45–95 | Khối 2: thẩm định pre-label 10 frame | Job có AI đã lưu, `decision_log.csv` ≥ 5 dòng |
| 95–105 | Nghỉ | |
| 105–115 | Export, dự đoán 3 số, `make lock` | Mã khóa gửi Lab Coach |
| 115–135 | Cài gói 1, `make profile`, đọc lỗi | `interpretation.md` |
| 135–155 | Sửa lại lỗi của mình | `rework_log.csv`, `assisted_rework.xml` |
| 155–165 | Nghỉ | |
| 165–195 | Xếp hạng 50 frame pool | `ranking.csv`, `ranking_rationale.md` |
| 195–205 | Bạn cặp kiểm, `make lock-ranking`, cài gói 2, `make al-eval` | `peer_check.md` |
| 205–220 | Debrief cả lớp | |
| 220–230 | Phản tư, `make check-submission`, nộp | `reflection.md` |
| 230–240 | Dự phòng hoặc stretch | |

Checkpoint: phút 30 xong ≥ 3 frame tay · phút 70 xong 6 frame đầu của job có AI · phút 180 mọi frame pool có điểm.
Chậm hơn thì báo Lab Coach; đừng bỏ qua xe để kịp giờ.

## Gói nộp

Mọi file nằm trong `submission/`. Mục 1–4 là tối thiểu cho mọi người. Mục 5–8 thuộc bài chính; hết giờ mà còn thiếu thì
báo Lab Coach.

| # | File | Tạo lúc |
|---|---|---|
| 1 | `manual_X.xml` (nhóm A) hoặc `manual_Y.xml` (nhóm B) | Export job làm tay |
| 2 | `assisted.xml` | Export job có AI |
| 3 | `decision_log.csv` (≥ 5 dòng của bạn) | Trong khối 2 |
| 4 | `states.json`, `prediction.md`, `lock.txt` | `make states`, bạn điền, `make lock` |
| 5 | `error_profile.csv`, `interpretation.md` | `make profile`, bạn viết |
| 6 | `rework_log.csv`, `assisted_rework.xml` | `make profile`, bạn điền và export lại |
| 7 | `ranking.csv`, `ranking_rationale.md`, `peer_check.md`, `lock_ranking.txt` | Bạn điền, `make lock-ranking` |
| 8 | `reflection.md` (4 câu) | Tạo khi `make profile`, bạn trả lời |

`make check-submission` báo file nào thiếu hoặc sai dạng. Lệnh này không chấm điểm.
Đọc [rubric 100 điểm](RUBRIC.md) để biết Lab Coach chấm bằng chứng và lập luận nào. Độ lớn của các chỉ số bias không phải điểm bài làm; rubric không đặt ngưỡng đạt/trượt chính thức.

## Card tra cứu

| Card | Mở khi |
|---|---|
| [Guideline](cards/guideline-card.md) | Trước khối 1; tra suốt buổi |
| [4 trạng thái](cards/four-states-card.md) | Phút 0–15, frame demo |
| [CVAT](cards/cvat-card.md) | Mở job, phím tắt, tag `not_reviewed`, export, Path B |
| [Từ vựng](cards/vocabulary-card.md) | Gặp từ lạ |
| [Sau khi khóa](cards/after-lock-card.md) | **Chỉ sau `make lock`** |
| [Pool](cards/pool-card.md) và [chi phí](cards/cost-card.md) | Phút 165, phần xếp hạng |
| [Stretch](cards/stretch-card.md) | Xong bài chính sớm |

## Luật chung

- **Khóa trước, xem đáp án sau.** Reference chỉ phát sau khi bạn gửi mã khóa. Sau `make lock`, các file đã khóa không sửa
  nữa; mọi lệnh sau kiểm lại mã và báo lỗi nếu file đổi.
- **Không push `reference/`.** `.gitignore` đã chặn thư mục này. Repo của bạn phải để private; chia sẻ đáp án
  cho bạn cùng lớp chưa khóa làm hỏng phép đo của họ.
- **Không sửa `data/`.** `make verify-data` kiểm từng file theo `data/SHA256SUMS`.
- **Ca card không nói tới:** ghi `escalated` vào `decision_log.csv` và hỏi Lab Coach. Không tự đặt luật.
- **Debrief không gắn tên.** Không hỏi bạn khác ra số nào.

## Trong repo

| Đường dẫn | Nội dung |
|---|---|
| `data/frames/lab/` | Frame demo `d01`, tập X, Y, C (17 frame) |
| `data/frames/pool/` | 50 frame chưa gán nhãn `p001`–`p050` |
| `data/prelabel/`, `data/cvat/` | Pre-label đã đóng băng (JSON và CVAT XML cho từng nhóm) |
| `data/pool/` | Thông tin frame pool, dự đoán của model, contact sheet, ngân sách |
| `data/manifest.csv` | Danh mục frame: tập, điều kiện, kích thước, sha256 |
| `lab8/` | Công cụ dòng lệnh (`make <lệnh>`) |
| `templates/` | Mẫu `make init` và `make profile` chép vào `submission/` |
| `reference/` | Rỗng lúc phát; `make install-reference` giải nén gói Lab Coach phát vào đây |

Repo này là bản phát hành từ `learner/` của pilot Day 8. Ảnh `cards/img/d01_reference.jpg` chỉ là lời giải của **frame demo d01** trong card bốn trạng thái; đáp án các frame bài tập và key honeypot không nằm trong repo học viên. Lab Coach phát hai gói reference theo các mốc khóa bài trong [GUIDE.md](GUIDE.md).

Nguồn ảnh, model và giấy phép: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
