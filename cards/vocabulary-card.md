# Thẻ từ vựng — Lab #08

| Từ | Nghĩa trong bài này | Số này **không** chứng minh |
|---|---|---|
| **pre-label** | Box do model sinh sẵn để người thẩm định. Ở đây: YOLO11n huấn luyện trên COCO, chưa học trên dữ liệu này, ngưỡng conf 0,40, đóng băng thành file | Không phải đáp án |
| **reference** | Box Lab Coach dùng để so. Chỉ phát **sau khi** bạn khóa bài | Không tuyệt đối đúng: thấy sai thì khiếu nại (`reference_disputed`) |
| **accepted / edited / deleted / added** | 4 trạng thái của một box sau khi bạn thẩm định ([card](four-states-card.md)) | Đúng hay sai |
| **accept rate** | accepted / số box pre-label | Chất lượng. Accept 99% có thể là soát kỹ, cũng có thể là không soát |
| **FP** (false positive) | Box AI không ứng với xe nào (bịa) | |
| **FN** (false negative) | Xe thật mà AI không có box (bỏ sót) | |
| **cls / loc** | Box đúng xe nhưng sai class / lệch vị trí (IoU < 0,5) | |
| **honeypot** | Một frame trong batch có AI mà Lab Coach cài sẵn lỗi vào pre-label. Bạn không biết là frame nào | Năng lực của bạn: một frame là quá ít để kết luận về một người |
| **bẫy hợp lý** | Box AI trông hợp lý nên người soát dừng tìm lỗi ([card](guideline-card.md#quét-trước)) | |
| **conf** | Điểm tin cậy của box. Điểm class là sigmoid độc lập từng lớp nên **không** là xác suất đúng: conf 0,9 không có nghĩa đúng 90% | Box lệch vị trí: conf chỉ đo phân loại |
| **least confidence** | Điểm bất định của một box = 1 − conf | |
| **margin** | p_top1 − p_top2: khoảng cách giữa hai class cao nhất. Nhỏ = model phân vân giữa hai class | |
| **aggregation (gộp)** | Đổi điểm từng box thành điểm frame: `sum` (cộng), `mean` (trung bình), `max` (lớn nhất) | |
| **scoring / sampling** | Scoring: chấm điểm từng box/frame. Sampling: chọn batch từ điểm đó, có loại trùng và gắn cờ | |
| **diversity (đa dạng)** | Batch không gồm nhiều frame gần như giống nhau (cùng video, cách nhau vài phần mười giây) | |
| **ngoại lai vô ích** | Frame điểm bất định cao nhưng gán nhãn cũng không dạy được gì (lóa đèn, xe chỉ còn vài pixel) | |
| **cold start** | Model chưa học gì trên dữ liệu mới nên điểm bất định của nó còn kém tin | |
| **proxy** | `make al-eval`: batch bạn chọn trỏ vào bao nhiêu lỗi model khác nhau, trên chi phí | Model sau khi học có tốt hơn không |

Các chỉ số dùng để đọc kết quả của chính bạn nằm ở [card sau khi khóa](after-lock-card.md). Mở card đó ở phút 115,
**sau** `make lock`.
