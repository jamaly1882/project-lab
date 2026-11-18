```python
import os
import sys
import socket
import threading
import time
import urllib.request
import datetime
import shutil

import webview


# ============================================================
# تحديد مجلد البرنامج
# ============================================================

if getattr(sys, "frozen", False):
    # عند تشغيل EXE
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # عند تشغيل Python مباشرة
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# إعدادات المشروع
# ============================================================

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erea.settings")

MANAGE = os.path.join(BASE_DIR, "manage.py")
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
BACKUP_PATH = os.path.join(BASE_DIR, "backup")

HOST = "127.0.0.1"
PORT = 8000

LOCK_PORT = 50000


# ============================================================
# منع تشغيل البرنامج مرتين
# ============================================================

lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    lock_socket.bind((HOST, LOCK_PORT))
except OSError:
    print("البرنامج يعمل بالفعل.")
    sys.exit(0)


# ============================================================
# إصلاح مسار المشروع عند التشغيل كـ EXE
# ============================================================

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.chdir(BASE_DIR)


# ============================================================
# النسخ الاحتياطي
# ============================================================

def backup_database():

    try:

        os.makedirs(BACKUP_PATH, exist_ok=True)

        if not os.path.exists(DB_PATH):
            print("قاعدة البيانات غير موجودة:")
            print(DB_PATH)
            return

        today = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_file = os.path.join(
            BACKUP_PATH,
            f"db_backup_{today}.sqlite3"
        )

        shutil.copy2(DB_PATH, backup_file)

        print("تم إنشاء النسخة الاحتياطية:")
        print(backup_file)

        backups = sorted(
            [
                f
                for f in os.listdir(BACKUP_PATH)
                if f.startswith("db_backup_")
                and f.endswith(".sqlite3")
            ],
            reverse=True
        )

        # الاحتفاظ بآخر 5 نسخ فقط
        for old in backups[5:]:
            try:
                os.remove(
                    os.path.join(BACKUP_PATH, old)
                )
            except Exception:
                pass

    except Exception as e:

        print("خطأ في النسخ الاحتياطي:")
        print(e)


# ============================================================
# تشغيل Django
# ============================================================

def start_django():

    try:

        from django.core.management import execute_from_command_line

        print("تشغيل Django...")

        execute_from_command_line(
            [
                MANAGE,
                "runserver",
                f"{HOST}:{PORT}",
                "--noreload",
            ]
        )

    except Exception as e:

        print("خطأ أثناء تشغيل Django:")
        print(e)


# ============================================================
# انتظار Django
# ============================================================

def wait_for_django(timeout=40):

    start = time.time()

    url = f"http://{HOST}:{PORT}/"

    while time.time() - start < timeout:

        try:

            urllib.request.urlopen(
                url,
                timeout=2
            )

            print("Django يعمل بنجاح.")
            return True

        except Exception:

            time.sleep(1)

    return False


# ============================================================
# API الخاصة بالواجهة
# ============================================================

class Api:

    def go_home(self):

        try:

            if webview.windows:
                webview.windows[0].load_url(
                    f"http://{HOST}:{PORT}/"
                )

        except Exception as e:
            print(e)


    def minimize_window(self):

        try:

            if webview.windows:
                webview.windows[0].minimize()

        except Exception as e:
            print(e)


    def close_window(self):

        try:

            for window in webview.windows:

                try:
                    window.destroy()
                except Exception:
                    pass

        finally:

            try:
                lock_socket.close()
            except Exception:
                pass

            os._exit(0)


# ============================================================
# البرنامج الرئيسي
# ============================================================

def main():

    print("=" * 60)
    print("نظام المساحة الإلكتروني")
    print("=" * 60)

    print("BASE_DIR:")
    print(BASE_DIR)

    print("DB:")
    print(DB_PATH)

    print("=" * 60)

    # النسخ الاحتياطي قبل التشغيل
    backup_database()

    # تشغيل Django
    django_thread = threading.Thread(
        target=start_django,
        daemon=True
    )

    django_thread.start()

    # انتظار Django
    if not wait_for_django():

        print("فشل تشغيل Django.")

        try:
            lock_socket.close()
        except Exception:
            pass

        sys.exit(1)

    # API
    api = Api()

    # WebView
    window = webview.create_window(
        "نظام المساحة الإلكتروني",
        f"http://{HOST}:{PORT}/",
        js_api=api,
        width=1100,
        height=750,
        min_size=(900, 600),
        resizable=True,
    )

    webview.start(
        debug=False
    )


# ============================================================
# تشغيل
# ============================================================

if __name__ == "__main__":
    main()
```
