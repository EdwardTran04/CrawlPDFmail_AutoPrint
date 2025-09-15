# 📧 Email PDF Downloader & Auto Printer

Hệ thống tự động tải PDF từ email và in tự động, được thiết kế để xử lý các email từ người gửi cụ thể và tự động in các file PDF.

## 🎯 Tổng quan

Dự án này bao gồm hai thành phần chính:

1. **`crawlPDF.py`** - Python script tự động tải PDF từ email IMAP
2. **`BatchPrintPDF.ps1`** - PowerShell script tự động in các file PDF đã tải

## ✨ Tính năng chính

### 📥 Email PDF Downloader
- ✅ Tự động kết nối IMAP và tải PDF từ email chưa đọc
- ✅ Lọc email theo người gửi cụ thể (`sender@gmail.com`)
- ✅ Tránh tải trùng lặp (mỗi email chỉ xử lý 1 lần)
- ✅ Đánh dấu email đã đọc sau khi xử lý
- ✅ Log chi tiết theo định dạng JSONL và text
- ✅ Hỗ trợ chạy định kỳ hoặc một lần
- ✅ Xử lý lỗi và timeout (30 giây)
- ✅ Tự động tạo tên file duy nhất nếu trùng tên
- ✅ **Logging nâng cao** với timestamp và level phân loại

### 🖨️ Auto PDF Printer
- ✅ Tự động phát hiện và in file PDF mới trong thư mục `In/`
- ✅ Hỗ trợ SumatraPDF (ưu tiên) và Adobe Reader (dự phòng)
- ✅ Tự động tìm kiếm ứng dụng PDF trong hệ thống
- ✅ Cấu hình máy in tùy chỉnh
- ✅ Di chuyển file đã in vào thư mục `_printed/`
- ✅ Xử lý lỗi in ấn chi tiết
- ✅ **Logging nâng cao** với timestamp và level phân loại

## 📁 Cấu trúc dự án

```
D:\Scripts\
├── crawlPDF.py                    # Script Python chính
├── BatchPrintPDF.ps1             # Script PowerShell in PDF
├── test.ps1                      # Script test (cấu hình khác)
├── requirements.txt              # Dependencies Python
├── README.md                     # Tài liệu này
├── secret/
│   └── secret.py                 # File cấu hình bí mật
├── In/                           # Thư mục chứa PDF đã tải
│   └── _printed/                 # Thư mục PDF đã in
├── log/                          # 📁 THƯ MỤC LOG CHUNG
│   ├── BatchPrintPDF_2024-01-15.log    # Log từ BatchPrintPDF.ps1
│   ├── email_pdf_downloader.log        # Log text từ crawlPDF.py
│   └── pdf_download_log.jsonl          # Log JSONL từ crawlPDF.py
└── processed_msg_ids.json        # Danh sách email đã xử lý
```

## 🚀 Cài đặt

### Yêu cầu hệ thống
- **Python 3.7+**
- **PowerShell 5.0+**
- **SumatraPDF** hoặc **Adobe Reader**
- **Máy in** được cài đặt và hoạt động

### 1. Cài đặt Python Dependencies

```bash
# Cài đặt nhanh
pip install schedule pytz

# Hoặc từ file requirements
pip install -r requirements.txt
```

### 2. Cấu hình Email

**Tạo App Password cho Gmail:**
1. Vào [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Tạo password mới cho ứng dụng

**Cập nhật file `secret/secret.py`:**
```python
EMAIL = "your_email@gmail.com"
PASSWORD = "your_app_password"  # App password, không phải password chính
IMAP_SERVER = "imap.gmail.com"
```

### 3. Cài đặt PDF Reader

**Cài đặt SumatraPDF (khuyến nghị):**
```bash
# Sử dụng winget
winget install SumatraPDF

# Hoặc tải từ: https://www.sumatrapdfreader.org/download-free-pdf-viewer.html
```

**Hoặc cài Adobe Reader:**
- Tải từ: https://get.adobe.com/reader/

### 4. Cấu hình Máy in

**Cập nhật cấu hình trong `BatchPrintPDF.ps1`:**
```powershell
$Printer = "Tên_Máy_In_Của_Bạn"  # Thay đổi tên máy in
$WatchFolder = "./Scripts/In"    # Thay đổi đường dẫn thư mục
```

## 📖 Sử dụng

### Chạy Email PDF Downloader

**Chạy một lần:**
```bash
python crawlPDF.py
```

**Chạy định kỳ:**
1. Sửa `RUN_CONTINUOUS = True` trong `crawlPDF.py`
2. Chạy: `python crawlPDF.py`

### Chạy Auto PDF Printer

**Chạy thủ công:**
```powershell
.\BatchPrintPDF.ps1
```

**Chạy tự động với Task Scheduler:**
1. Mở **Task Scheduler** (taskschd.msc)
2. Tạo task mới
3. **Trigger**: Every 1 minute
4. **Action**: Start a program
5. **Program**: `powershell.exe`
6. **Arguments**: `-File "D:\Scripts\BatchPrintPDF.ps1"`

## ⚙️ Cấu hình

### Email Downloader Settings

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `SENDER_FILTER_EMAIL` | Email người gửi cần lọc | `sender@gmail.com` |
| `MAILBOXES` | Danh sách mailbox cần quét | `["INBOX"]` |
| `DOWNLOAD_DIR` | Thư mục lưu PDF | `In` |
| `LOG_DIR` | Thư mục lưu log | `log` |
| `RUN_CONTINUOUS` | Chạy liên tục | `False` |
| `INTERVAL_MINUTES` | Khoảng thời gian chạy (phút) | `5` |
| `socket.setdefaulttimeout()` | Timeout kết nối (giây) | `30` |

### Printer Settings

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `$WatchFolder` | Thư mục theo dõi PDF | `./Scripts/In` |
| `$DoneFolder` | Thư mục PDF đã in | `./Scripts/In/_printed` |
| `$LogFolder` | Thư mục lưu log | `./log` |
| `$Printer` | Tên máy in | `Canon LBP6030/6040/6018L` |
| `$minAge` | Thời gian chờ tối thiểu (giây) | `0` |

## 📊 Log và Monitoring

### 📁 Cấu trúc Log

Tất cả log được lưu trong thư mục `log/` chung:

```
log/
├── BatchPrintPDF_2024-01-15.log    # Log từ BatchPrintPDF.ps1 (theo ngày)
├── email_pdf_downloader.log        # Log text từ crawlPDF.py
└── pdf_download_log.jsonl          # Log JSONL từ crawlPDF.py
```

### 📝 Log Format

**PowerShell Log (BatchPrintPDF.ps1):**
```
[2024-01-15 14:30:25] [INFO] Watch: ./Scripts/In
[2024-01-15 14:30:25] [INFO] Printer: Canon LBP6030/6040/6018L
[2024-01-15 14:30:25] [INFO] Found 3 PDF(s), 2 ready (> 0s)
[2024-01-15 14:30:25] [INFO] Starting print process for 2 files
[2024-01-15 14:30:25] [INFO] Printing: document1.pdf
[2024-01-15 14:30:30] [SUCCESS] Successfully printed and moved: document1.pdf
[2024-01-15 14:30:30] [INFO] Print process completed
```

**Python Log (crawlPDF.py):**
```
2024-01-15 14:30:25,123 [INFO] Khởi động Email PDF Downloader
2024-01-15 14:30:25,124 [INFO] Chế độ chạy: Một lần
2024-01-15 14:30:25,125 [INFO] === BẮT ĐẦU CRAWL PDF ===
2024-01-15 14:30:25,126 [INFO] Kết nối IMAP server: imap.gmail.com
2024-01-15 14:30:25,127 [INFO] Email: your-email@gmail.com
2024-01-15 14:30:25,128 [INFO] Lọc từ sender: sender@gmail.com
2024-01-15 14:30:30,456 [INFO] Đăng nhập IMAP thành công
2024-01-15 14:30:35,789 [INFO] [INBOX] Không có email UNSEEN từ sender@gmail.com.
2024-01-15 14:30:35,790 [INFO] === KẾT THÚC CRAWL PDF ===
```

**JSONL Log Format:**
```json
{
  "fetched_at": "2025-01-15T14:30:25+07:00",
  "mailbox": "INBOX",
  "message_unique_id": "<message-id>",
  "from": "Sender Name <email@domain.com>",
  "subject": "Email Subject",
  "saved_files": ["filename.pdf"],
  "status": "success",
  "error": null
}
```

### 🏷️ Log Levels

- **INFO** - Thông tin chung, hoạt động bình thường
- **SUCCESS** - Thành công (in file, tải PDF)
- **ERROR** - Lỗi xảy ra
- **WARNING** - Cảnh báo

### 📈 Trạng thái Status (JSONL)

- `success` - Tải PDF thành công
- `no_pdf` - Email không có PDF
- `error` - Có lỗi xảy ra

## 🔧 Troubleshooting

### Debug Mode

**Bật debug IMAP:**
```python
imaplib.Debug = 1  # Trong crawlPDF.py
```

**Kiểm tra cài đặt:**
```bash
python -c "import schedule, pytz; print('Dependencies installed successfully!')"
```

### Kiểm tra Log

**Xem log mới nhất:**
```bash
# PowerShell
Get-Content "log\BatchPrintPDF_$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 20

# Python log
Get-Content "log\email_pdf_downloader.log" -Tail 20
```

**Xem log JSONL:**
```bash
# Xem 5 dòng cuối
Get-Content "log\pdf_download_log.jsonl" -Tail 5 | ConvertFrom-Json
```

## 🚀 Quick Start

1. **Cài đặt dependencies:**
   ```bash
   pip install schedule pytz
   ```

2. **Cấu hình email trong `secret/secret.py`**

3. **Cài đặt SumatraPDF:**
   ```bash
   winget install SumatraPDF
   ```

4. **Chạy thử:**
   ```bash
   python crawlPDF.py
   ```

5. **Chạy printer:**
   ```powershell
   .\BatchPrintPDF.ps1
   ```

6. **Kiểm tra log:**
   ```bash
   # Xem log trong thư mục log/
   dir log\
   ```

## 📋 Changelog

### v2.0 - Logging System Upgrade
- ✅ **Tích hợp hệ thống logging thống nhất** - Tất cả log được lưu trong thư mục `log/` chung
- ✅ **Logging nâng cao** - Thêm timestamp, level phân loại (INFO, SUCCESS, ERROR, WARNING)
- ✅ **Cải thiện PowerShell logging** - Thay thế Write-Host bằng function Write-Log chuyên dụng
- ✅ **Cải thiện Python logging** - Cấu hình logging chi tiết với file và console handler
- ✅ **Log theo ngày** - File log PowerShell được tạo theo ngày để dễ quản lý
- ✅ **Encoding UTF-8** - Hỗ trợ đầy đủ tiếng Việt trong log

### v1.0 - Initial Release
- ✅ Email PDF downloader với IMAP
- ✅ Auto PDF printer với PowerShell
- ✅ Cấu hình linh hoạt
- ✅ Xử lý lỗi cơ bản

---

**💡 Tip:** Sử dụng Task Scheduler để chạy cả hai script tự động, và kiểm tra thư mục `log/` để theo dõi hoạt động của hệ thống!