# Card 4 trạng thái — worked example trên frame demo `d01`

Khi thẩm định pre-label, mỗi box cuối cùng rơi vào **đúng một** trong 4 trạng thái. `make states` tự tính bằng cách so
bản export của bạn với file pre-label đóng băng; bạn không phải tự đếm, nhưng phải hiểu mỗi thao tác của mình ra
trạng thái nào.

| Trạng thái | Bạn làm gì trong CVAT | Script nhận ra thế nào |
|---|---|---|
| `accepted` | Để nguyên box AI | Box còn nguyên chỗ (IoU ≥ 0,99) và cùng class |
| `edited` | Kéo lại box, hoặc đổi class | Vẫn ghép được với box AI cũ nhưng đổi hình hoặc class |
| `deleted` | Xóa box AI | Box AI không còn trong bản của bạn |
| `added` | Vẽ box mới | Box của bạn không ghép với box AI nào |

Bốn trạng thái mô tả **hành vi sửa**, không nói đúng hay sai. Accepted nhiều không có nghĩa là làm tốt: một box sai
mà bạn để nguyên cũng là `accepted`.

## Làm lại từng bước (phút 0–15)

Mở [img/d01_prelabel.jpg](img/d01_prelabel.jpg) (box vàng = AI). Chưa nhìn ảnh reference.

1. **Đọc box AI**: 12 box. Ẩn chúng đi.
2. **So ảnh gốc**: quét trái → phải, gần → xa theo [card guideline](guideline-card.md#quét-trước). Đếm xe thấy
   khoảng một nửa trở lên, ngoài vùng xám.
3. **Gọi tên trạng thái** cho từng box, bật lại lớp AI và so với số bạn đếm:
   - Xe trắng cắt mép trái (x ≈ 0–60), AI gọi `others` → dáng thân hộp, mui cao → `van` → **edited**.
   - Xe đen dưới đáy ảnh (x ≈ 666–818) không có box AI → **added**.
   - Xe buýt trắng giữa ảnh có **hai** box AI (`bus` và `others`) → xóa box `others` → **deleted**.
   - Xe đen bên trái (x ≈ 122–211) nằm một phần trong vùng xám → không chắc tâm ở đâu → **escalated** (ca mơ hồ).
   - Các box còn lại đúng xe, đúng class, ôm vừa → **accepted**.
4. **Ghi luật**: mỗi quyết định đáng chú ý là một dòng `decision_log.csv`, cột `rule_or_reason` trích mục card.
   Bốn dòng mẫu `d01` có sẵn trong `submission/decision_log.csv` sau `make init`.

Giờ mở [img/d01_reference.jpg](img/d01_reference.jpg) (box xanh = reference) và so. Reference có box cho xe đen dưới
đáy ảnh, không có box cho xe bên trái trong vùng xám. Box reference và box AI không trùng từng pixel: ghép ở IoU ≥ 0,5
nên vẫn là đúng.

## Tự làm trên frame đầu tiên của bạn

Làm đúng 4 bước trên với frame đầu tiên của khối có AI. Viết một dòng log của chính bạn. Xong khi dòng đó đủ cột
như dòng mẫu và cột lý do trích một mục cụ thể của card.

## Cặp đối chiếu

[img/contrast_van_vs_car.jpg](img/contrast_van_vs_car.jpg): trái — AI gọi `others`, reference là `van`; phải — AI gọi
`car`, reference là `car`. Khi gặp hai ca giống nhau mà kết luận khác nhau, ghi **một đặc điểm nhìn thấy trên ảnh**
làm chúng khác (vd "mui cao liền khối tới đuôi"), không ghi "trông giống".
