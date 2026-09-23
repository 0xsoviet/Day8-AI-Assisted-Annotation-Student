# Cost card — phần (c) xếp hạng 50 frame

Bạn nhận **một** kịch bản (ghi trong `submission/info.json`). Hai kịch bản có ngân sách tương đương về tiền.

| Kịch bản | Trả tiền theo | Ngân sách | Chi phí một frame |
|---|---|---|---|
| **S1** | ảnh | **10 frame** | 1 |
| **S2** | box | **103 box** (= 10 × 10.32 box trung bình mỗi frame của pool) | số dòng của frame đó trong `pool_predictions.csv` |

- Chi phí S2 là **ước lượng** theo số box model thấy (conf ≥ 0.25). Số box thật người gán nhãn phải vẽ sẽ khác;
  `make al-eval` in cả hai.
- Cách tính chi phí đổi được thứ hạng các chiến lược chọn mẫu (arXiv:2205.07708). Vì vậy hàm gộp điểm theo frame
  (`sum` / `mean` / `max`) phải chọn **theo kịch bản của bạn**, và bạn phải nói vì sao.
- `selected = 1` trong `ranking.csv` là batch bạn gửi đi gán nhãn; tổng chi phí không được vượt ngân sách.
