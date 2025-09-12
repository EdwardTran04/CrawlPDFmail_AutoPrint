# -*- coding: utf-8 -*-
"""
Email PDF Downloader (filtered by sender)
----------------------------------------
- Chỉ lấy PDF từ email UNSEEN gửi bởi SENDER_FILTER_EMAIL.
- Mỗi email chỉ xử lý 1 lần (Message-ID hoặc UID).
- Lưu PDF vào thư mục DOWNLOAD_DIR.
- Log JSONL: thời gian, ID thư, from, subject, file đã lưu, trạng thái, lỗi (nếu có).
- Đánh dấu mail đã đọc (Seen) bằng UID STORE để tránh treo/không tương thích.
"""

import os
import re
import json
import time
import socket
import logging
import imaplib
import email
from email import policy
from email.header import decode_header
from datetime import datetime
from pathlib import Path
import pytz

import schedule
from secret import secret  # cần secret.IMAP_SERVER / secret.EMAIL / secret.PASSWORD

# ================== CẤU HÌNH ==================
IMAP_SERVER = (secret.IMAP_SERVER or "").strip()
EMAIL = (secret.EMAIL or "").strip()
PASSWORD = (secret.PASSWORD or "").strip()

# ĐỊA CHỈ NGƯỜI GỬI CẦN LỌC
SENDER_FILTER_EMAIL = "sender@gmail.com"

# Mailbox cần quét
MAILBOXES = ["INBOX"]

# Thư mục tải PDF
DOWNLOAD_DIR = Path("In")
# File ghi các ID đã xử lý
PROCESSED_IDS_FILE = Path("processed_msg_ids.json")
# Log JSONL theo yêu cầu
LOG_JSONL_FILE = Path("pdf_download_log.jsonl")
# Log text để vận hành
LOG_FILE = "email_pdf_downloader.log"

# Lịch chạy (đặt RUN_CONTINUOUS=True để chạy vòng lặp mỗi INTERVAL_MINUTES phút)
RUN_CONTINUOUS = False
INTERVAL_MINUTES = 5

# Timeout tránh treo socket
socket.setdefaulttimeout(30)  # giây

# (Tùy chọn) debug IMAP chi tiết
imaplib.Debug = 0

# Tạo thư mục tải nếu chưa có
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ================== LOGGING ==================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


# ================== TIỆN ÍCH ==================
def load_processed_ids():
    try:
        with open(PROCESSED_IDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_processed_ids(processed_ids: set):
    try:
        with open(PROCESSED_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(processed_ids)), f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("Lỗi ghi PROCESSED_IDS_FILE")


def append_jsonl(record: dict):
    try:
        with open(LOG_JSONL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logging.exception("Lỗi ghi LOG_JSONL_FILE")


def now_vn_iso():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(tz=tz).isoformat(timespec="seconds")


def decode_mime_str(s):
    """Giải mã header MIME (Subject, Filename, ...) về Unicode."""
    if not s:
        return ""
    parts = decode_header(s)
    decoded = []
    for content, enc in parts:
        if isinstance(content, bytes):
            try:
                decoded.append(content.decode(enc or "utf-8", errors="replace"))
            except Exception:
                decoded.append(content.decode("utf-8", errors="replace"))
        else:
            decoded.append(content)
    return "".join(decoded)


def sanitize_filename(name: str, maxlen: int = 150) -> str:
    name = (name or "").strip().replace("\n", " ").replace("\r", " ")
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > maxlen:
        root, ext = os.path.splitext(name)
        name = root[: maxlen - len(ext)] + ext
    return name or "attachment.pdf"


def unique_path(base_dir: Path, filename: str) -> Path:
    p = base_dir / filename
    if not p.exists():
        return p
    stem, ext = os.path.splitext(filename)
    i = 1
    while True:
        cand = base_dir / f"{stem}({i}){ext}"
        if not cand.exists():
            return cand
        i += 1


def is_pdf_bytes(data: bytes) -> bool:
    # PDF chuẩn bắt đầu bằng "%PDF"
    return isinstance(data, (bytes, bytearray)) and data[:4] == b"%PDF"


def fetch_uid(mail, email_id_bytes) -> str:
    """Lấy UID cho email hiện tại để fallback nếu không có Message-ID."""
    try:
        typ, resp = mail.fetch(email_id_bytes, "(UID)")
        if typ == "OK" and resp and isinstance(resp[0], tuple):
            m = re.search(rb"UID\s+(\d+)", resp[0][1])
            if m:
                return m.group(1).decode()
    except Exception:
        logging.exception("Không lấy được UID")
    try:
        return f"SEQ-{email_id_bytes.decode()}"
    except Exception:
        return f"SEQ-{repr(email_id_bytes)}"


def mark_seen(mail, email_id_bytes):
    """
    Đánh dấu Seen bền vững:
    - Thử UID STORE trước
    - Nếu lỗi, fallback sequence STORE
    - Flags chuẩn: '(\Seen)'
    """
    uid = fetch_uid(mail, email_id_bytes)
    try:
        typ, _ = mail.uid('STORE', uid, '+FLAGS', r'(\Seen)')
        if typ != 'OK':
            raise RuntimeError(f'UID STORE failed: {typ}')
    except Exception as e:
        logging.warning(f'UID STORE lỗi ({e}), fallback sequence STORE')
        seq = email_id_bytes.decode(errors='ignore')
        mail.store(seq, '+FLAGS', r'(\Seen)')


# ================== XỬ LÝ EMAIL ==================
def process_unseen_pdfs_in_mailbox(mail, mailbox: str) -> dict:
    """
    Quét 1 mailbox:
    - Tìm UNSEEN TỪ SENDER_FILTER_EMAIL
    - Tải PDF
    - Ghi log JSONL
    - Đánh dấu đã đọc + lưu processed_ids
    Trả về thống kê.
    """
    stats = {"mailbox": mailbox, "emails_seen": 0, "emails_processed": 0, "pdf_saved": 0}
    processed_ids = load_processed_ids()

    # Chọn mailbox
    typ, _ = mail.select(mailbox)
    if typ != "OK":
        logging.error(f"Không thể select mailbox: {mailbox}")
        return stats

    # ======= CHỈ LẤY UNSEEN TỪ ĐỊA CHỈ CỤ THỂ =======
    # Cách 1: IMAP chuẩn
    search_query = f'(UNSEEN FROM "{SENDER_FILTER_EMAIL}")'
    status, messages = mail.search(None, search_query)
    if status != "OK":
        logging.error(f"SEARCH thất bại ở {mailbox} với query: {search_query}")
        return stats

    email_ids = messages[0].split()
    if not email_ids:
        logging.info(f"[{mailbox}] Không có email UNSEEN từ {SENDER_FILTER_EMAIL}.")
        return stats

    for email_id in email_ids:
        unique_id = None
        saved_files = []
        error_msg = None

        try:
            logging.info(f"[{mailbox}] FETCH email ID: {email_id.decode(errors='ignore')}")
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                raise RuntimeError("FETCH RFC822 thất bại")

            # Parse email
            raw_email = None
            for part in msg_data:
                if isinstance(part, tuple):
                    raw_email = part[1]
                    break
            if raw_email is None:
                raise RuntimeError("Không nhận được nội dung RFC822")

            msg = email.message_from_bytes(raw_email, policy=policy.default)

            # Unique key: ưu tiên Message-ID, fallback UID
            msg_id = msg.get("Message-ID")
            unique_id = (msg_id or "").strip() or f"UID-{fetch_uid(mail, email_id)}"

            # Bỏ qua nếu đã xử lý
            if unique_id in processed_ids:
                logging.info(f"[{mailbox}] Bỏ qua (đã xử lý): {unique_id}")
                mark_seen(mail, email_id)
                stats["emails_seen"] += 1
                continue

            from_hdr = decode_mime_str(msg.get("From"))
            subject = decode_mime_str(msg.get("Subject"))

            # Duyệt các part để lấy PDF
            for part in msg.walk():
                if part.is_multipart():
                    continue

                ctype = (part.get_content_type() or "").lower()
                filename = part.get_filename()
                filename = decode_mime_str(filename) if filename else None
                payload = part.get_payload(decode=True) or b""

                looks_like_pdf = (ctype == "application/pdf")
                if not looks_like_pdf and filename:
                    looks_like_pdf = filename.lower().endswith(".pdf")

                if not looks_like_pdf and payload:
                    # Bắt PDF bị gắn application/octet-stream
                    if is_pdf_bytes(payload):
                        looks_like_pdf = True
                        if not filename:
                            filename = "attachment.pdf"

                if looks_like_pdf and payload:
                    base_name = filename or "attachment.pdf"
                    short_subject = sanitize_filename(subject)[:60]
                    suggested = sanitize_filename(base_name)
                    if short_subject and short_subject not in suggested:
                        stem, ext = os.path.splitext(suggested)
                        suggested = (
                            sanitize_filename(f"{stem} - {short_subject}{ext}")
                            if ext
                            else sanitize_filename(f"{suggested} - {short_subject}.pdf")
                        )

                    target_path = unique_path(DOWNLOAD_DIR, suggested)
                    with open(target_path, "wb") as f:
                        f.write(payload)
                    saved_files.append(target_path.name)
                    stats["pdf_saved"] += 1
                    logging.info(f"[{mailbox}] Đã lưu PDF: {target_path}")

            # Ghi log (kể cả không có PDF)
            status_str = "success" if saved_files else "no_pdf"
            record = {
                "fetched_at": now_vn_iso(),
                "mailbox": mailbox,
                "message_unique_id": unique_id,
                "from": from_hdr,
                "subject": subject,
                "saved_files": saved_files,
                "status": status_str,
                "error": None
            }
            append_jsonl(record)

            # Đánh dấu Seen & lưu processed_ids
            mark_seen(mail, email_id)
            processed_ids.add(unique_id)
            save_processed_ids(processed_ids)

            stats["emails_processed"] += 1

        except Exception as e:
            logging.exception(f"[{mailbox}] Lỗi khi xử lý email")
            error_msg = str(e)
            try:
                # Vẫn đánh dấu đã đọc để đảm bảo "mỗi mail chỉ lấy 1 lần"
                mark_seen(mail, email_id)
            except Exception:
                logging.exception(f"[{mailbox}] Không thể đánh dấu Seen")

            if unique_id:
                processed_ids.add(unique_id)
                save_processed_ids(processed_ids)

            record = {
                "fetched_at": now_vn_iso(),
                "mailbox": mailbox,
                "message_unique_id": unique_id or f"SEQ-{email_id.decode(errors='ignore')}",
                "from": None,
                "subject": None,
                "saved_files": [],
                "status": "error",
                "error": error_msg
            }
            append_jsonl(record)

        # Đếm số email đã chạm tới
        stats["emails_seen"] += 1

    return stats


def process_unseen_pdfs(mail) -> dict:
    """Quét tuần tự các mailbox trong MAILBOXES."""
    totals = {"emails_seen": 0, "emails_processed": 0, "pdf_saved": 0, "by_mailbox": []}
    for mbox in MAILBOXES:
        stats = process_unseen_pdfs_in_mailbox(mail, mbox)
        totals["by_mailbox"].append(stats)
        totals["emails_seen"] += stats["emails_seen"]
        totals["emails_processed"] += stats["emails_processed"]
        totals["pdf_saved"] += stats["pdf_saved"]
    return totals


def job():
    """Một lần chạy: kết nối, đăng nhập, quét, đóng kết nối."""
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        totals = process_unseen_pdfs(mail)
        logging.info(f"Tổng kết: {totals}")
        print("Done. Summary:", totals)
    except Exception:
        logging.exception("Lỗi kết nối/điều khiển IMAP trong job()")
    finally:
        if mail is not None:
            try:
                try:
                    mail.close()
                except Exception:
                    pass
                mail.logout()
            except Exception:
                pass


# ================== CHẠY ==================
if __name__ == "__main__":
    if RUN_CONTINUOUS:
        schedule.every(INTERVAL_MINUTES).minutes.do(job)
        job()  # chạy ngay lần đầu
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        job()
