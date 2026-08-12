# Benj Cursor Maker — Neon Pixel Edition

Ứng dụng Windows desktop để cắt ảnh/GIF và tạo con trỏ chuột `.cur`, `.ani` cùng gói cursorpack (kèm `install.bat` tự cài). Giao diện PyQt6 phong cách retro 16-bit; mọi thao tác phóng/thu đều dùng **Nearest-Neighbor** để giữ nguyên pixel art. Giao diện hỗ trợ **tiếng Việt / tiếng Anh** (nút EN/VN góc trên phải).

## Tính năng

- Import PNG, GIF, JPG/JPEG, BMP — GIF động có Play/Pause và thanh chọn frame (giữ duration từng frame).
- Kéo chuột trực tiếp trên ảnh để chọn vùng crop, Grid Snap OFF/16/32/48 px.
- Click một pixel chính xác để đặt **Hotspot** (kèm zoom + pan đồng bộ hai khung xem).
- Xuất `.cur` (static) và `.ani` chuẩn RIFF/ACON (động, giữ timing từng frame).
- **Cursorpack Builder**: gán `.cur`/`.ani` hoặc gán thẳng cursor đang chỉnh vào 15 trạng thái Windows (Normal, Help, Text, Busy…); nút **Apply** lưu tạm để gán tiếp, **Save** xuất thư mục pack có `install.inf` + `install.bat` tự cài và kích hoạt.
- **Preview cursor khi hover** trong Cursorpack Builder: rê chuột lên từng trạng thái là thấy đúng cursor đã gán (kể cả animation), chưa gán thì không hiện.
- Không cần xuất file trước khi gán: crop + hotspot hiện tại được gán thẳng vào trạng thái Windows.

## Yêu cầu

- Windows 10/11 64-bit.
- Python **3.11** trở lên (chỉ cần cho lần chạy đầu tiên).

## Chạy (portable)

Double-click **`run.bat`** — không cần cài đặt gì:

- Lần đầu: tự tạo môi trường `.venv`, tự cài dependencies rồi mở app.
- Các lần sau: mở app ngay, **không hiện cửa sổ cmd**.

Hoặc chạy thủ công:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Cách sử dụng

1. Bấm **MỞ ẢNH** (IMPORT), chọn ảnh hoặc GIF.
2. Với GIF: **PHÁT/TẠM DỪNG** hoặc kéo thanh frame.
3. Chọn Grid Snap rồi kéo trên ảnh để khoanh vùng; bấm **CẮT VÙNG** (APPLY CROP) — vùng crop áp dụng cho mọi frame.
4. Trong ô HOTSPOT, click pixel làm điểm chạm của cursor (đồng bộ mọi frame).
5. **XUẤT .CUR** cho frame hiện tại, hoặc **XUẤT .ANI** cho toàn bộ animation.
6. **GÓI CURSOR** (CURSORPACK): chọn trạng thái → gán thẳng cursor đang chỉnh (GÁN CURSOR HIỆN TẠI) hoặc từ file (GÁN .CUR / .ANI). **Apply** lưu tạm và đóng để chỉnh ảnh gán tiếp; **Save** xuất pack.

## Cài cursorpack trên Windows

App xuất thẳng một **thư mục mang tên scheme** (không nén):

1. Save → chọn thư mục cha → app tạo `<Tên pack>/` chứa `install.bat`, `install.inf`, `README.txt` và các cursor.
2. Mở thư mục đó, double-click `install.bat` → **Yes** khi Windows hỏi quyền Administrator.
3. Script tự copy cursor vào `%WINDIR%\Cursors\<Tên pack>`, đăng ký và kích hoạt scheme, refresh Windows. Không hiện cửa sổ cmd.

> Windows có thể cảnh báo vì installer không có chữ ký số. Script chỉ thao tác trong phạm vi cursor scheme của user hiện tại.

## Kiểm thử

```bash
.venv\Scripts\python.exe -m pytest -q
```

## Cấu trúc

```
main.py              # entry point
ui.py                # toàn bộ widget/giao diện + luồng tương tác
image_processor.py   # load frame, crop, grid snap, Nearest-Neighbor resize
exporter.py          # writer CUR/ANI/install.inf/install.bat, parser ANI, xuất cursorpack
i18n.py              # bảng dịch tiếng Việt / tiếng Anh
tooltip_style.py     # vô hiệu hoá animation tooltip hệ thống
tests/               # test định dạng nhị phân, pixel, smoke test UI
run.bat              # launcher portable (tự tạo venv, chạy ẩn)
```

## Lưu ý định dạng

- Cursor Windows tối đa 256×256 px — ảnh lớn hơn được thu bằng Nearest-Neighbor.
- `.cur` dùng DIB BGRA 32-bit + AND mask, kèm hotspot.
- `.ani` đóng gói frame CUR trong RIFF/ACON, duration quy đổi sang tick 1/60 giây theo chuẩn Windows.
