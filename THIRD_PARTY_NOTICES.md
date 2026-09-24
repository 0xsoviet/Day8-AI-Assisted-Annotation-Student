# Third-party notices — Day 8

## Ảnh

Ảnh trong `data/frames/` là frame trích từ **UA-DETRAC** qua bản phát hành lại
[`abhineet123/ua_detrac`](https://huggingface.co/datasets/abhineet123/ua_detrac) trên Hugging Face. Thẻ dữ liệu của bản
phát hành lại ghi giấy phép CC BY 4.0. Trang gốc UA-DETRAC hiện không truy cập được, và các bản sao khác ghi giấy phép khác
nhau (CC BY 4.0 hoặc CC BY-NC-SA 3.0). Repo này ghi nhận bằng chứng đó, không đưa ra kết luận pháp lý.

Lab Coach đã tô xám các vùng ignore của UA-DETRAC, đổi tên frame và xáo thứ tự. Ảnh không được xử lý thêm.

- [Bài báo UA-DETRAC](https://faculty.ucmerced.edu/mhyang/papers/cviu2020_detrac.pdf) (Wen et al., CVIU 2020)

## Pre-label và dự đoán trên pool

`data/prelabel/`, `data/cvat/` và `data/pool/pool_predictions.csv` là output của `yolo11n.pt`
([Ultralytics](https://docs.ultralytics.com/), mô hình COCO chưa fine-tune), chạy trên CPU rồi đóng băng thành file.
Trong buổi lab, notebook Colab chạy YOLO11n thật trên **frame demo `d01`** ở hai ngưỡng confidence. Output đó chỉ để học cách kiểm dự đoán; không thay pre-label đã đóng băng của 10 frame bài chính.

## Phần mềm

- [CVAT](https://github.com/cvat-ai/cvat) — công cụ gán nhãn; định dạng export CVAT for images 1.1.
- [Google Colab](https://research.google.com/colaboratory/faq.html) — môi trường chạy notebook; tài nguyên và thời lượng phiên có thể thay đổi.
- [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/) — mô hình chạy trong notebook trên frame demo.
- Package `lab8/` chỉ dùng thư viện chuẩn của Python.

Việc dùng từng phần mềm tuân theo giấy phép và điều khoản tại nguồn tương ứng.
