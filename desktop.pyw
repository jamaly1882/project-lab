import webview
import os
import sqlite3
import threading
import datetime
import shutil
import sys

# ==============================
# مسارات الملفات
# ==============================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
BACKUP_PATH = os.path.join(BASE_DIR, "backup")
HTML_PATH = os.path.join(BASE_DIR, "html")  # ملفات واجهة المستخدم

# ==============================
# النسخ الاحتياطي
# ==============================
def backup_database():
    os.makedirs(BACKUP_PATH, exist_ok=True)
    if not os.path.exists(DB_PATH):
        print(f"[خطأ] قاعدة البيانات {DB_PATH} غير موجودة")
        return
    today = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_PATH, f"db_backup_{today}.sqlite3")
    shutil.copy2(DB_PATH, backup_file)
    # حذف النسخ القديمة
    backups = sorted([f for f in os.listdir(BACKUP_PATH) if f.startswith("db_backup_")], reverse=True)
    for old in backups[5:]:
        os.remove(os.path.join(BACKUP_PATH, old))

# ==============================
# API للتفاعل مع WebView
# ==============================
class Api:
    def go_home(self):
        webview.windows[0].load_url("file://"+os.path.join(HTML_PATH, "index.html"))
    def minimize_window(self):
        webview.windows[0].minimize()
    def close_window(self):
        for w in webview.windows:
            try: w.destroy()
            except: pass
        sys.exit(0)

# ==============================
# مثال وظيفة قاعدة بيانات
# ==============================
def get_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM your_table LIMIT 10")  # عدّل حسب جدولك
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==============================
# تشغيل الواجهة
# ==============================
def start_desktop():
    api = Api()
    window = webview.create_window(
        "نظام المساحة الإلكتروني",
        "file://"+os.path.join(HTML_PATH, "index.html"),
        js_api=api,
        width=1100,
        height=750
    )
    window.events.closing += lambda: api.close_window()
    webview.start()

# ==============================
# البرنامج الرئيسي
# ==============================
if __name__ == "__main__":
    backup_database()
    threading.Thread(target=start_desktop, daemon=True).start()