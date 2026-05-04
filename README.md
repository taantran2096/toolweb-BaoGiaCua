# Báo Giá Cửa & Rào CNC – Web Application

Ứng dụng web tạo báo giá PDF chuyên nghiệp cho cửa &amp; rào CNC.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy ứng dụng

```bash
python app.py
```

Mở trình duyệt: **http://localhost:5000**

> **Ghi chú:** Debug mode mặc định tắt. Để bật trong quá trình phát triển: `FLASK_DEBUG=1 python app.py`

## Tính năng

- ✅ Tạo, chỉnh sửa, xóa báo giá
- ✅ Bảng hạng mục: tự động tính diện tích &amp; thành tiền
- ✅ Xem trước báo giá (giao diện A4 chuẩn)
- ✅ Xuất PDF chuyên nghiệp (ReportLab)
- ✅ Lưu/load dữ liệu JSON
- ✅ Giao diện thân thiện, responsive

## Cấu trúc

```
toolweb-BaoGiaCua/
├── app.py               # Flask backend
├── pdf_generator.py     # Tạo PDF (ReportLab)
├── requirements.txt
├── templates/
│   ├── index.html       # Danh sách báo giá
│   ├── edit.html        # Form nhập/chỉnh sửa
│   └── preview.html     # Xem trước A4
├── static/
│   ├── style.css
│   ├── script.js        # Tính toán tự động
│   └── logo.png
└── data/
    └── quotes.json      # Dữ liệu lưu trữ
```
