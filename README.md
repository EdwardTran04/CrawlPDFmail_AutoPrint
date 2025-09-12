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
- ✅ Log chi tiết theo định dạng JSONL
- ✅ Hỗ trợ chạy định kỳ hoặc một lần
- ✅ Xử lý lỗi và timeout (30 giây)
- ✅ Tự động tạo tên file duy nhất nếu trùng tên

### 🖨️ Auto PDF Printer
- ✅ Tự động phát hiện và in file PDF mới trong thư mục `In/`
- ✅ Hỗ trợ SumatraPDF (ưu tiên) và Adobe Reader (dự phòng)
- ✅ Tự động tìm kiếm ứng dụng PDF trong hệ thống
- ✅ Cấu hình máy in tùy chỉnh
- ✅ Di chuyển file đã in vào thư mục `_printed/`
- ✅ Xử lý lỗi in ấn chi tiết

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
├── processed_msg_ids.json        # Danh sách email đã xử lý
├── pdf_download_log.jsonl        # Log chi tiết JSONL
└── email_pdf_downloader.log      # Log vận hành
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
| `SENDER_FILTER_EMAIL` | Email người gửi cần lọc | `minhquanqni2004@gmail.com` |
| `MAILBOXES` | Danh sách mailbox cần quét | `["INBOX"]` |
| `DOWNLOAD_DIR` | Thư mục lưu PDF | `In` |
| `RUN_CONTINUOUS` | Chạy liên tục | `False` |
| `INTERVAL_MINUTES` | Khoảng thời gian chạy (phút) | `5` |
| `socket.setdefaulttimeout()` | Timeout kết nối (giây) | `30` |

### Printer Settings

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `$WatchFolder` | Thư mục theo dõi PDF | `C:/Scripts/In` |
| `$Printer` | Tên máy in | `Canon LBP6030/6040/6018L` |
| `$minAge` | Thời gian chờ tối thiểu (giây) | `0` |

## 📊 Log và Monitoring

### Log Files

1. **`email_pdf_downloader.log`** - Log vận hành chi tiết
2. **`pdf_download_log.jsonl`** - Log JSONL cho mỗi email xử lý
3. **`processed_msg_ids.json`** - Danh sách email đã xử lý

### Log Format (JSONL)

```json
{
  "fetched_at": "2025-09-10T11:44:24+07:00",
  "mailbox": "INBOX",
  "message_unique_id": "<message-id>",
  "from": "Sender Name <email@domain.com>",
  "subject": "Email Subject",
  "saved_files": ["filename.pdf"],
  "status": "success",
  "error": null
}
```

### Trạng thái Status
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

