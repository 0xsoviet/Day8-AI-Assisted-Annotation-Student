# Báo cáo Lab Ngày 08: Học chủu động cho bộ phát hiện xe

Họ và tên: Đào Xuân Tùng

Công cụ gán nhãn đã dùng: CVAT (Computer Vision Annotation Tool) — gán nhãn online, xuất định dạng YOLO, sau đó chạy `tools/pack_labels.py` để đóng gói lại thành `day8_data.zip` và nạp lên Colab.

## 1. Dữ liệu và cách chia tập

Video được quay từ camera cố định nhìn xuống đường cao tốc ban đêm. Tập pool và tập test được chia theo trục thời gian — pool lấy phần đầu video, test lấy phần cuối, với một vùng đệm ở giữa không được dùng. Cách chia này phản ánh đúng môi trường triển khai thực tế của xe tự lái VinFast: mô hình luôn phải dự đoán trên cảnh tương lai chưa từng thấy, không phải trên cảnh ngẫu nhiên xen kẽ đã nhìn qua trong lúc train.

Nếu chia ngẫu nhiên, hai ảnh chụp cách nhau 0.4 giây (gần như trùng lặp) sẽ nằm ở cả hai tập. Khi đó tập test "rò rỉ" thông tin hình ảnh vào tập train — mô hình học thuộc vị trí xe ở từng giây thay vì học cách nhận diện xe nói chung — và AP50 trên test sẽ bị thổi phồng không phản ánh khả năng tổng quát hóa thật sự.

## 2. Mô hình khởi đầu lạnh (cold start)

| vòng | model | ảnh train | box train | AP50 | Δ AP50 so cold start | P@0.25 | R@0.25 | F1 | R small | R medium | R large |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | yolov8n cold start (COCO car+bus+truck) | 0 | 0 | 0.771 | — | 0.925 | 0.489 | 0.640 | 0.182 | 0.547 | 0.561 |

Mô hình khởi đầu lạnh đạt Precision 0.925 nhưng Recall chỉ 0.489 — tức là những gì nó khoanh thì đúng, nhưng bỏ sót hơn một nửa số xe thật. Vấn đề rõ nhất khi xem `compare_round0.jpg` là xe nhỏ (hai chấm đèn ở xa): Recall nhóm small chỉ 0.182 — 4 trên 5 xe nhỏ bị bỏ qua. Nguyên nhân là `yolov8n` được huấn luyện trên COCO ban ngày với đủ texture thân xe; ở video ban đêm, xe xa chỉ còn hai điểm sáng không đủ feature. Nhóm medium và large cũng bị bỏ sót đáng kể (Recall ~0.55), chủ yếu do nhiều xe bị che khuất một phần hoặc chìm vào nền tối.

Một trường hợp cần người rà lại nhãn tham chiếu trước khi kết luận mô hình sai: box nhãn tham chiếu cho xe ở góc khuất có thể được vẽ hơi rộng hơn guideline (ôm cả bóng tối quanh thân xe), làm IoU tính được thấp hơn ngưỡng 0.5 ngay cả khi mô hình khoanh đúng vị trí xe. Trước khi kết luận mô hình nhầm, cần kiểm tra từng box FN theo kiểu này.

## 3. Chiến lược chọn mẫu

Công thức `score = W_U·U + W_A·A + W_D·D` kết hợp ba tín hiệu: **U** (độ bất định trung bình của 5 box khó nhất, W=0.5) đo mức model đang lưỡng lự giữa phát hiện và bỏ qua; **A** (số box mơ hồ conf 0.15–0.5 chuẩn hóa, W=0.3) đo mật độ xe model không chắc; **D** (khoảng cách thời gian tới ảnh đã gán nhãn gần nhất, tối đa 10 giây, W=0.2) ưu tiên cảnh chưa được "phủ sóng" theo thời gian. `MIN_GAP_S=2.0s` loại bỏ ảnh quá gần ảnh đã chọn trong cùng lô, tránh gán nhãn hai lần cùng một cảnh.

Ba frame minh họa từ `SELECTION.md` vòng 1: frame_0099.jpg (U=0.856, A=0.833, score đầu bảng) có đủ xe tải che khuất mà model phân vân; frame_0326.jpg (score 0.916, A=1.0) là frame mật độ xe cao nhất trong lô 12 ảnh; frame_0331.jpg (score 0.915) chứa nhiều xe khuất sau nhau khiến model tạo ra nhiều FP cột đèn đường đồng thời FN xe thật. Đối chiếu với frame_0187.jpg (được tôi quét trước trong BLIND_SCAN: 27 xe, A=1.0): model chỉ đề xuất 14 box nhưng sau sửa có 26, cho thấy mật độ FN cao thực sự tương quan với điểm A cao.

Điểm bất định không chứng minh sửa ảnh đó sẽ cải thiện mô hình, vì mô hình có thể phân vân do nhiễu ánh sáng hoặc cảnh lạ hoàn toàn, không phải vì thiếu nhãn. Cải thiện thực sự chỉ xác nhận được sau khi train lại và so sánh trên tập test cố định.

## 4. Các vòng học chủ động (active learning)

| vòng | model | ảnh train | box train | AP50 | Δ AP50 so cold start | P@0.25 | R@0.25 | F1 | R small | R medium | R large |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | yolov8n cold start (COCO car+bus+truck) | 0 | 0 | 0.771 | — | 0.925 | 0.489 | 0.640 | 0.182 | 0.547 | 0.561 |
| 1 | yolov8n fine-tune vong 1..1 | 12 | 355 | 0.742 | -0.029 | 1.000 | 0.268 | 0.423 | 0.000 | 0.287 | 0.561 |

**Vòng 1** — 12 ảnh, 355 box sau sửa (model đề xuất 169, tôi giữ 138 accepted, sửa 17 edited, xóa 14 FP, thêm 200 FN mới; accept rate 82%). AP50 giảm 0.029 so với cold start. Precision tăng lên 1.000 nhưng Recall sụt từ 0.489 xuống 0.268. Nhóm small Recall = 0.000, medium giảm từ 0.547 xuống 0.287, large giữ nguyên 0.561.

Nguyên nhân Recall sụt mạnh: fine-tune trên chỉ 12 ảnh với 355 box đã "hướng" mô hình học rất chặt vào style gán nhãn của 12 ảnh đó (mật độ xe cao, điều kiện đèn đặc thù). Khi chạy trên 20 ảnh test có phân bố cảnh đa dạng hơn, mô hình trở nên rất thận trọng — chỉ dự đoán khi cực kỳ chắc, dẫn đến Precision = 1.0 nhưng bỏ sót hầu hết xe. Đây là hiện tượng overfitting trên tập train nhỏ, không phải do nhãn sai.

Một ca kết quả đổi chiều sau fine-tune: trong `compare_round1.jpg` ở cảnh frame_0270 (khu vực giao lộ nhiều xe), cold start tạo ra 3 FP (xe máy và biển hiệu) nhưng nhận đủ xe con — sau vòng 1, mô hình không tạo FP nào nhưng bỏ sót 60% xe. Lý do có thể kiểm: nhãn vòng 1 tập trung ở cảnh đường thẳng, mô hình học "xe thật ở đường thẳng mới có conf cao" nên hạ conf ở cảnh giao lộ phức tạp.

Quan sát độc lập từ BLIND_SCAN.md (frame_0187.jpg, 27 xe, trước khi xem pre-label): hai vị trí bỏ sót dự đoán là góc dưới phải (xe di chuyển nhanh, nhoè thành cụm đen) và góc giữa dưới cùng (xe bị cắt do góc camera). Sau sửa nhãn (REVIEW_LOG.csv, vòng 1 frame_0187): đúng hai vị trí đó tôi thêm box mới. Vòng 1 fine-tune vẫn không cải thiện recall nhóm này vì chỉ có 1 ảnh với 2 ca đặc biệt — quá ít để mô hình học được pattern xe nhoè và xe bị cắt mép.

## 5. Kết luận và giới hạn

Vòng 1 cho AP50 = 0.742, giảm 0.029 so với cold start 0.771. Kết quả này cho thấy fine-tune trên 12 ảnh chưa đủ để vượt baseline, và hiện tượng Precision = 1.0 / Recall = 0.268 là dấu hiệu của over-conservative model sau overfitting ngắn. Tôi sẽ tiếp tục vòng 2 với lô 12 ảnh mới từ `selection_round2.csv`, ưu tiên cảnh đa dạng hơn (góc rộng, mật độ xe thấp, xe xa).

Hai ca còn yếu cho vòng sau: (1) xe nhoè do chuyển động nhanh ở góc tối — chi phí rà nhãn cao vì khó xác định đường viền, nguy cơ ảnh gần trùng thấp vì xe di chuyển; (2) xe ở rất xa chỉ còn hai chấm đèn — chi phí thấp nhưng nguy cơ bị bỏ qua khi chấm điểm (box nhỏ dưới 16px không tính), cần cân nhắc xem thêm nhãn loại này có giúp AP50 tăng hay không.

Giới hạn: tập test chỉ 20 ảnh nên độ lệch chuẩn của AP50 lớn; chênh lệch 0.029 có thể nằm trong biên độ nhiễu thống kê. Quy tắc bỏ qua box nhỏ dưới 16px ưu tiên xe gần hơn xe xa, phù hợp với ưu tiên an toàn của xe tự lái VinFast nhưng làm số liệu không phản ánh toàn bộ khả năng nhận diện. Nhãn tham chiếu test được tạo có hỗ trợ của mô hình và chưa được rà 100% thủ công — một số xe góc khuất có thể bị bỏ sót trong nhãn tham chiếu, làm TP bị đếm nhầm thành FP khi mô hình tìm đúng xe đó. Nếu AP50 giảm ở vòng sau, tôi sẽ kiểm tra trước: (a) phân bố cảnh trong lô ảnh mới có đại diện cho tập test không; (b) có FP nào là do nhãn tham chiếu bị thiếu không; (c) loss curve trong `runs/round*/` có cho thấy underfitting hay overfitting không.
