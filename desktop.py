# -*- coding: utf-8 -*-

import os
import sys
import time
import socket
import shutil
import datetime
import threading
import traceback

import webview


# ============================================================
# الإعدادات
# ============================================================

PORT = 8000

LOCK_PORT = 50000

APP_NAME = "نظام المساحة الإلكتروني"


# ============================================================
# تحديد مكان البرنامج
# ============================================================

if getattr(sys, "frozen", False):

    EXE_DIR = os.path.dirname(
        os.path.abspath(
            sys.executable
        )
    )

    BUNDLE_DIR = getattr(
        sys,
        "_MEIPASS",
        EXE_DIR
    )

else:

    EXE_DIR = os.path.dirname(
        os.path.abspath(
            __file__
        )
    )

    BUNDLE_DIR = EXE_DIR


# ============================================================
# المسار القابل للكتابة
# ============================================================

BASE_DIR = EXE_DIR


# ============================================================
# Python Path
# ============================================================

if BUNDLE_DIR not in sys.path:

    sys.path.insert(
        0,
        BUNDLE_DIR
    )


if BASE_DIR not in sys.path:

    sys.path.insert(
        0,
        BASE_DIR
    )


# ============================================================
# قاعدة البيانات
# ============================================================

DB_PATH = os.path.join(
    BASE_DIR,
    "db.sqlite3"
)


# ============================================================
# النسخ الاحتياطية
# ============================================================

BACKUP_PATH = os.path.join(
    BASE_DIR,
    "backup"
)


# ============================================================
# Media
# ============================================================

MEDIA_PATH = os.path.join(
    BASE_DIR,
    "media"
)


# ============================================================
# Session
# ============================================================

SESSION_PATH = os.path.join(
    BASE_DIR,
    "session"
)


# ============================================================
# Log
# ============================================================

LOG_PATH = os.path.join(
    BASE_DIR,
    "desktop.log"
)


# ============================================================
# كتابة Log
# ============================================================

def write_log(message):

    try:

        with open(
            LOG_PATH,
            "a",
            encoding="utf-8"
        ) as file:

            file.write("\n")

            file.write(
                "=" * 70
            )

            file.write("\n")

            file.write(
                datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            file.write("\n")

            file.write(
                str(message)
            )

            file.write("\n")

    except Exception:

        pass


# ============================================================
# منع تشغيل أكثر من نسخة
# ============================================================

lock_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)


try:

    lock_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    lock_socket.bind(
        (
            "127.0.0.1",
            LOCK_PORT
        )
    )

    lock_socket.listen(1)

except OSError:

    write_log(
        "البرنامج يعمل بالفعل."
    )

    sys.exit(0)


# ============================================================
# Django Error
# ============================================================

django_error = None


# ============================================================
# إنشاء المجلدات
# ============================================================

def prepare_directories():

    directories = [

        BACKUP_PATH,

        MEDIA_PATH,

        SESSION_PATH,

    ]


    for directory in directories:

        try:

            os.makedirs(
                directory,
                exist_ok=True
            )

        except Exception:

            write_log(
                f"تعذر إنشاء المجلد: {directory}"
            )


# ============================================================
# تهيئة قاعدة البيانات
# ============================================================

def prepare_database():

    try:

        os.makedirs(
            BASE_DIR,
            exist_ok=True
        )


        # ====================================================
        # قاعدة البيانات الخارجية موجودة
        # ====================================================

        if os.path.exists(
            DB_PATH
        ):

            write_log(
                "[OK] قاعدة البيانات موجودة:"
            )

            write_log(
                DB_PATH
            )

            return


        # ====================================================
        # قاعدة البيانات المضمنة داخل EXE
        # ====================================================

        first_run_db = os.path.join(
            BUNDLE_DIR,
            "db.sqlite3"
        )


        if os.path.exists(
            first_run_db
        ):

            shutil.copy2(
                first_run_db,
                DB_PATH
            )

            write_log(
                "[OK] تم استخراج قاعدة البيانات."
            )

            return


        # ====================================================
        # لا توجد قاعدة بيانات
        # ====================================================

        write_log(
            "[INFO] لا توجد قاعدة بيانات."
        )


    except Exception:

        write_log(
            "[ERROR] DATABASE"
        )

        write_log(
            traceback.format_exc()
        )


# ============================================================
# النسخ الاحتياطي
# ============================================================

def backup_database():

    try:

        os.makedirs(
            BACKUP_PATH,
            exist_ok=True
        )


        if not os.path.exists(
            DB_PATH
        ):

            write_log(
                "[INFO] قاعدة البيانات غير موجودة."
            )

            return


        now = datetime.datetime.now()


        filename = (

            "db_backup_"

            + now.strftime(
                "%Y%m%d_%H%M%S"
            )

            + ".sqlite3"

        )


        backup_file = os.path.join(

            BACKUP_PATH,

            filename

        )


        shutil.copy2(

            DB_PATH,

            backup_file

        )


        write_log(
            "[OK] Backup:"
        )

        write_log(
            backup_file
        )


        # ====================================================
        # الاحتفاظ بآخر 5 نسخ
        # ====================================================

        backups = sorted(

            [

                f

                for f in os.listdir(
                    BACKUP_PATH
                )

                if (

                    f.startswith(
                        "db_backup_"
                    )

                    and

                    f.endswith(
                        ".sqlite3"
                    )

                )

            ],

            reverse=True

        )


        for old_backup in backups[5:]:

            try:

                os.remove(
                    os.path.join(
                        BACKUP_PATH,
                        old_backup
                    )
                )

            except Exception:

                pass


    except Exception:

        write_log(
            "[ERROR] BACKUP"
        )

        write_log(
            traceback.format_exc()
        )


# ============================================================
# تشغيل Django
# ============================================================

def start_django():

    global django_error


    try:

        # ====================================================
        # Settings
        # ====================================================

        os.environ.setdefault(

            "DJANGO_SETTINGS_MODULE",

            "erea.settings"

        )


        # ====================================================
        # Python Path
        # ====================================================

        if BUNDLE_DIR not in sys.path:

            sys.path.insert(
                0,
                BUNDLE_DIR
            )


        # ====================================================
        # Django
        # ====================================================

        from django.core.management import (
            execute_from_command_line
        )


        # ====================================================
        # Arguments
        # ====================================================

        sys.argv = [

            "desktop_django",

            "runserver",

            f"127.0.0.1:{PORT}",

            "--noreload",

            "--insecure",

        ]


        # ====================================================
        # Log
        # ====================================================

        write_log(
            "========================================"
        )

        write_log(
            "تشغيل Django"
        )

        write_log(
            "========================================"
        )

        write_log(
            f"EXE_DIR = {EXE_DIR}"
        )

        write_log(
            f"BUNDLE_DIR = {BUNDLE_DIR}"
        )

        write_log(
            f"DB_PATH = {DB_PATH}"
        )

        write_log(
            f"MEDIA_PATH = {MEDIA_PATH}"
        )

        write_log(
            "DJANGO_SETTINGS_MODULE = erea.settings"
        )

        write_log(
            f"PORT = {PORT}"
        )


        # ====================================================
        # تشغيل Django
        # ====================================================

        execute_from_command_line(
            sys.argv
        )


    except Exception as error:

        django_error = error


        write_log(
            "========================================"
        )

        write_log(
            "ERROR DJANGO"
        )

        write_log(
            "========================================"
        )

        write_log(
            str(error)
        )

        write_log(
            traceback.format_exc()
        )


# ============================================================
# انتظار Django
# ============================================================

def wait_for_django(
    timeout=60
):

    start = time.time()


    while (

        time.time() - start

        < timeout

    ):

        if django_error is not None:

            write_log(
                "Django توقف بسبب خطأ."
            )

            return False


        try:

            sock = socket.create_connection(

                (
                    "127.0.0.1",
                    PORT
                ),

                timeout=2

            )


            sock.close()


            write_log(
                "[OK] Django PORT يعمل."
            )


            return True


        except OSError:

            time.sleep(1)


    write_log(
        "[ERROR] انتهى انتظار Django بدون فتح المنفذ."
    )


    return False


# ============================================================
# API
# ============================================================

class Api:

    def go_home(self):

        try:

            if webview.windows:

                webview.windows[0].load_url(

                    f"http://127.0.0.1:{PORT}/"

                )

        except Exception:

            write_log(
                traceback.format_exc()
            )


    def minimize_window(self):

        try:

            if webview.windows:

                webview.windows[0].minimize()

        except Exception:

            write_log(
                traceback.format_exc()
            )


    def close_window(self):

        try:

            for window in webview.windows:

                try:

                    window.destroy()

                except Exception:

                    pass

        except Exception:

            pass

        finally:

            try:

                lock_socket.close()

            except Exception:

                pass


# ============================================================
# إغلاق WebView
# ============================================================

def on_closed():

    write_log(
        "تم إغلاق WebView."
    )


    try:

        lock_socket.close()

    except Exception:

        pass


# ============================================================
# Main
# ============================================================

def main():

    try:

        write_log(
            "========================================"
        )

        write_log(
            APP_NAME
        )

        write_log(
            "========================================"
        )


        # ====================================================
        # المجلدات
        # ====================================================

        prepare_directories()


        # ====================================================
        # قاعدة البيانات
        # ====================================================

        prepare_database()


        # ====================================================
        # Backup
        # ====================================================

        backup_database()


        # ====================================================
        # Django Thread
        # ====================================================

        django_thread = threading.Thread(

            target=start_django,

            daemon=True

        )


        django_thread.start()


        write_log(
            "انتظار Django..."
        )


        # ====================================================
        # انتظار السيرفر
        # ====================================================

        if not wait_for_django(60):

            if django_error:

                write_log(
                    "Django ERROR:"
                )

                write_log(
                    str(django_error)
                )

            else:

                write_log(
                    "Django لم يبدأ خلال 60 ثانية."
                )

            return


        write_log(
            "[OK] Django يعمل."
        )


        # ====================================================
        # URL
        # ====================================================

        url = (
            f"http://127.0.0.1:{PORT}/"
        )


        write_log(
            "URL:"
        )

        write_log(
            url
        )


        # ====================================================
        # API
        # ====================================================

        api = Api()


        # ====================================================
        # WebView
        # ====================================================

        write_log(
            "إنشاء نافذة WebView..."
        )


        webview.create_window(

            APP_NAME,

            url,

            js_api=api,

            width=1100,

            height=750,

            min_size=(
                900,
                600
            ),

            resizable=True,

        )


        write_log(
            "تم إنشاء نافذة WebView."
        )


        # ====================================================
        # Start WebView
        # ====================================================

        webview.start(
            debug=False
        )


        write_log(
            "WebView انتهى."
        )


    except Exception:

        write_log(
            "========================================"
        )

        write_log(
            "MAIN ERROR"
        )

        write_log(
            "========================================"
        )

        write_log(
            traceback.format_exc()
        )


    finally:

        on_closed()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()