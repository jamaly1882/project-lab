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
# UTF-8
# ============================================================

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"


# ============================================================
# LOCALHOST / PROXY
#
# منع أي Proxy أو إعداد شبكة من التأثير على الاتصال المحلي
# ============================================================

os.environ["NO_PROXY"] = (
    "127.0.0.1,"
    "localhost,"
    "::1"
)

os.environ["no_proxy"] = (
    "127.0.0.1,"
    "localhost,"
    "::1"
)


# ============================================================
# SETTINGS
# ============================================================

PORT = 8000

LOCK_PORT = 50000

APP_NAME = "نظام المساحة الإلكتروني"


# ============================================================
# FROZEN
# ============================================================

IS_FROZEN = bool(
    getattr(
        sys,
        "frozen",
        False
    )
)


# ============================================================
# EXE DIR
# ============================================================

if IS_FROZEN:

    EXE_DIR = os.path.dirname(
        os.path.abspath(
            sys.executable
        )
    )

    BUNDLE_DIR = os.path.abspath(
        getattr(
            sys,
            "_MEIPASS",
            EXE_DIR
        )
    )

else:

    EXE_DIR = os.path.dirname(
        os.path.abspath(
            __file__
        )
    )

    BUNDLE_DIR = EXE_DIR


# ============================================================
# BASE DIR
# ============================================================

BASE_DIR = EXE_DIR


# ============================================================
# ENV
# ============================================================

os.environ[
    "EREA_APP_DIR"
] = BASE_DIR


os.environ[
    "DJANGO_SETTINGS_MODULE"
] = "erea.settings"


# ============================================================
# PYTHON PATH
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
# PATHS
# ============================================================

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "db.sqlite3"
)


INITIAL_DATABASE_PATH = os.path.join(
    BUNDLE_DIR,
    "db.sqlite3"
)


MEDIA_PATH = os.path.join(
    BASE_DIR,
    "media"
)


INITIAL_MEDIA_IMAGES_PATH = os.path.join(
    BUNDLE_DIR,
    "media",
    "images"
)


MEDIA_IMAGES_PATH = os.path.join(
    MEDIA_PATH,
    "images"
)


BACKUP_PATH = os.path.join(
    BASE_DIR,
    "backup"
)


SESSION_PATH = os.path.join(
    BASE_DIR,
    "session"
)


STATIC_PATH = os.path.join(
    BASE_DIR,
    "static"
)


LOG_PATH = os.path.join(
    BASE_DIR,
    "logs"
)


# ============================================================
# LOG FILE
# ============================================================

LOG_FILE = os.path.join(
    LOG_PATH,
    "desktop.log"
)


def write_log(message):

    try:

        os.makedirs(
            LOG_PATH,
            exist_ok=True
        )

        timestamp = (
            datetime.datetime.now()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        text = (
            f"[{timestamp}] "
            f"{message}"
        )

        with open(
            LOG_FILE,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                text + "\n"
            )

    except Exception:

        pass


# ============================================================
# DIRECTORIES
# ============================================================

def prepare_directories():

    directories = [

        BASE_DIR,

        MEDIA_PATH,

        MEDIA_IMAGES_PATH,

        BACKUP_PATH,

        SESSION_PATH,

        STATIC_PATH,

        LOG_PATH,

    ]


    for directory in directories:

        try:

            os.makedirs(
                directory,
                exist_ok=True
            )

        except Exception:

            write_log(
                "ERROR CREATING DIRECTORY:"
            )

            write_log(
                directory
            )

            write_log(
                traceback.format_exc()
            )


# ============================================================
# DATABASE
# ============================================================

def prepare_database():

    try:

        write_log(
            "================================"
        )

        write_log(
            "PREPARE DATABASE"
        )

        write_log(
            f"DATABASE_PATH = "
            f"{DATABASE_PATH}"
        )

        write_log(
            f"INITIAL_DATABASE_PATH = "
            f"{INITIAL_DATABASE_PATH}"
        )


        # ----------------------------------------------------
        # قاعدة البيانات الخارجية موجودة
        # ----------------------------------------------------

        if os.path.isfile(
            DATABASE_PATH
        ):

            write_log(
                "DATABASE ALREADY EXISTS"
            )

            return True


        # ----------------------------------------------------
        # البحث عن قاعدة البيانات داخل Bundle
        # ----------------------------------------------------

        if not os.path.isfile(
            INITIAL_DATABASE_PATH
        ):

            write_log(
                "INITIAL DATABASE NOT FOUND"
            )

            return False


        # ----------------------------------------------------
        # نسخ قاعدة البيانات
        # ----------------------------------------------------

        shutil.copy2(

            INITIAL_DATABASE_PATH,

            DATABASE_PATH

        )


        write_log(
            "INITIAL DATABASE COPIED"
        )

        write_log(
            f"FROM: "
            f"{INITIAL_DATABASE_PATH}"
        )

        write_log(
            f"TO: "
            f"{DATABASE_PATH}"
        )

        return True


    except Exception:

        write_log(
            "ERROR prepare_database"
        )

        write_log(
            traceback.format_exc()
        )

        return False


# ============================================================
# MEDIA IMAGES
# ============================================================

def prepare_media_images():

    try:

        os.makedirs(
            MEDIA_IMAGES_PATH,
            exist_ok=True
        )


        write_log(
            "================================"
        )

        write_log(
            "PREPARE MEDIA IMAGES"
        )

        write_log(
            f"INITIAL = "
            f"{INITIAL_MEDIA_IMAGES_PATH}"
        )

        write_log(
            f"DESTINATION = "
            f"{MEDIA_IMAGES_PATH}"
        )


        # ----------------------------------------------------
        # لا توجد صور داخل Bundle
        # ----------------------------------------------------

        if not os.path.isdir(
            INITIAL_MEDIA_IMAGES_PATH
        ):

            write_log(
                "NO INITIAL MEDIA IMAGES"
            )

            return True


        copied_count = 0

        skipped_count = 0

        error_count = 0


        # ----------------------------------------------------
        # نسخ الصور والمجلدات الداخلية
        # ----------------------------------------------------

        for root, dirs, files in os.walk(

            INITIAL_MEDIA_IMAGES_PATH

        ):

            for filename in files:

                source = os.path.join(
                    root,
                    filename
                )


                relative_path = os.path.relpath(

                    source,

                    INITIAL_MEDIA_IMAGES_PATH

                )


                destination = os.path.join(

                    MEDIA_IMAGES_PATH,

                    relative_path

                )


                destination_dir = os.path.dirname(
                    destination
                )


                os.makedirs(

                    destination_dir,

                    exist_ok=True

                )


                # ------------------------------------------------
                # الصورة موجودة مسبقاً
                # ------------------------------------------------

                if os.path.isfile(
                    destination
                ):

                    skipped_count += 1

                    continue


                # ------------------------------------------------
                # نسخ الصورة
                # ------------------------------------------------

                try:

                    shutil.copy2(

                        source,

                        destination

                    )

                    copied_count += 1

                    write_log(
                        f"COPIED: {source}"
                    )

                    write_log(
                        f"TO: {destination}"
                    )

                except Exception:

                    error_count += 1

                    write_log(
                        "ERROR COPYING IMAGE"
                    )

                    write_log(
                        f"SOURCE: {source}"
                    )

                    write_log(
                        f"DESTINATION: {destination}"
                    )

                    write_log(
                        traceback.format_exc()
                    )


        # ----------------------------------------------------
        # النتيجة
        # ----------------------------------------------------

        write_log(
            "================================"
        )

        write_log(
            "MEDIA IMAGES RESULT"
        )

        write_log(
            f"MEDIA COPIED = "
            f"{copied_count}"
        )

        write_log(
            f"MEDIA SKIPPED = "
            f"{skipped_count}"
        )

        write_log(
            f"MEDIA ERRORS = "
            f"{error_count}"
        )


        return (
            error_count == 0
        )


    except Exception:

        write_log(
            "ERROR prepare_media_images"
        )

        write_log(
            traceback.format_exc()
        )

        return False


# ============================================================
# WKHTMLTOPDF
# ============================================================

def check_wkhtmltopdf():

    candidates = [

        # ----------------------------------------------------
        # داخل PyInstaller Bundle
        # ----------------------------------------------------

        os.path.join(
            BUNDLE_DIR,
            "wkhtmltopdf",
            "bin",
            "wkhtmltopdf.exe"
        ),

        # ----------------------------------------------------
        # بجانب EXE
        # ----------------------------------------------------

        os.path.join(
            BASE_DIR,
            "wkhtmltopdf",
            "bin",
            "wkhtmltopdf.exe"
        ),

        # ----------------------------------------------------
        # تثبيت النظام
        # ----------------------------------------------------

        r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe",

    ]


    write_log(
        "================================"
    )

    write_log(
        "CHECK WKHTMLTOPDF"
    )


    for path in candidates:

        write_log(
            f"CHECK WKHTML: {path}"
        )


        if os.path.isfile(
            path
        ):

            # ------------------------------------------------
            # متغير البرنامج
            # ------------------------------------------------

            os.environ[
                "WKHTMLTOPDF_CMD"
            ] = path


            # ------------------------------------------------
            # إضافة مجلد wkhtmltopdf إلى PATH
            # ------------------------------------------------

            wkhtml_dir = os.path.dirname(
                path
            )


            current_path = os.environ.get(
                "PATH",
                ""
            )


            if wkhtml_dir not in current_path:

                os.environ[
                    "PATH"
                ] = (

                    wkhtml_dir
                    + os.pathsep
                    + current_path

                )


            write_log(
                f"WKHTML FOUND: {path}"
            )


            return path


    write_log(
        "WKHTMLTOPDF NOT FOUND"
    )

    return None


# ============================================================
# BACKUP
# ============================================================

def backup_database():

    try:

        if not os.path.isfile(
            DATABASE_PATH
        ):

            write_log(
                "BACKUP SKIPPED - DATABASE NOT FOUND"
            )

            return False


        os.makedirs(
            BACKUP_PATH,
            exist_ok=True
        )


        timestamp = (
            datetime.datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )


        backup_file = os.path.join(

            BACKUP_PATH,

            f"db_{timestamp}.sqlite3"

        )


        shutil.copy2(

            DATABASE_PATH,

            backup_file

        )


        write_log(
            f"BACKUP CREATED: "
            f"{backup_file}"
        )


        # ----------------------------------------------------
        # الاحتفاظ بآخر 5 نسخ
        # ----------------------------------------------------

        backups = sorted(

            [

                os.path.join(
                    BACKUP_PATH,
                    name
                )

                for name in os.listdir(
                    BACKUP_PATH
                )

                if name.lower().endswith(
                    ".sqlite3"
                )

            ],

            key=lambda p:
                os.path.getmtime(p),

            reverse=True

        )


        for old_file in backups[5:]:

            try:

                os.remove(
                    old_file
                )

            except Exception:

                pass


        return True


    except Exception:

        write_log(
            "ERROR backup_database"
        )

        write_log(
            traceback.format_exc()
        )

        return False


# ============================================================
# START DJANGO
# ============================================================

def start_django():

    django_start_time = time.time()


    try:

        os.environ[
            "DJANGO_SETTINGS_MODULE"
        ] = "erea.settings"


        write_log(
            "================================"
        )

        write_log(
            "START DJANGO"
        )


        write_log(
            f"DJANGO SETTINGS = "
            f"{os.environ.get('DJANGO_SETTINGS_MODULE')}"
        )


        write_log(
            f"BASE_DIR = "
            f"{BASE_DIR}"
        )


        write_log(
            f"BUNDLE_DIR = "
            f"{BUNDLE_DIR}"
        )


        # ----------------------------------------------------
        # Django
        # ----------------------------------------------------

        from django.core.management import (
            execute_from_command_line
        )


        write_log(
            "DJANGO IMPORTED"
        )


        # ----------------------------------------------------
        # تشغيل Django
        # ----------------------------------------------------

        execute_from_command_line([

            "manage.py",

            "runserver",

            f"127.0.0.1:{PORT}",

            "--noreload",

            "--insecure",

        ])


    except Exception:

        write_log(
            "ERROR DJANGO"
        )

        write_log(
            traceback.format_exc()
        )


    finally:

        elapsed = (
            time.time()
            - django_start_time
        )


        write_log(
            f"DJANGO THREAD ENDED "
            f"AFTER {elapsed:.2f} SEC"
        )


# ============================================================
# WAIT FOR DJANGO
#
# مهم:
# لا نقوم بفتح الصفحة الرئيسية هنا.
#
# نتحقق فقط من أن المنفذ 8000 أصبح مفتوحاً.
#
# هذا يمنع الصفحة الرئيسية من أن تُنفذ مرتين:
#
# 1. مرة أثناء الانتظار
# 2. مرة داخل WebView
#
# ============================================================

def wait_for_django(
    timeout=60
):

    start = time.time()


    write_log(
        "================================"
    )

    write_log(
        "WAITING FOR DJANGO PORT"
    )


    while (
        time.time() - start
        < timeout
    ):

        sock = None


        try:

            # ------------------------------------------------
            # إنشاء Socket
            # ------------------------------------------------

            sock = socket.socket(

                socket.AF_INET,

                socket.SOCK_STREAM

            )


            sock.settimeout(
                0.5
            )


            # ------------------------------------------------
            # الاتصال بـ localhost
            # ------------------------------------------------

            result = sock.connect_ex(

                (
                    "127.0.0.1",
                    PORT
                )

            )


            # ------------------------------------------------
            # إغلاق Socket
            # ------------------------------------------------

            sock.close()

            sock = None


            # ------------------------------------------------
            # المنفذ أصبح جاهزاً
            # ------------------------------------------------

            if result == 0:

                elapsed = (
                    time.time()
                    - start
                )


                write_log(
                    "DJANGO PORT READY"
                )


                write_log(
                    f"PORT = {PORT}"
                )


                write_log(
                    f"READY AFTER "
                    f"{elapsed:.2f} SEC"
                )


                return True


        except Exception:

            if sock is not None:

                try:

                    sock.close()

                except Exception:

                    pass


        time.sleep(
            0.2
        )


    # --------------------------------------------------------
    # Timeout
    # --------------------------------------------------------

    elapsed = (
        time.time()
        - start
    )


    write_log(
        "DJANGO PORT TIMEOUT"
    )


    write_log(
        f"TIMEOUT AFTER "
        f"{elapsed:.2f} SEC"
    )


    return False


# ============================================================
# WEBVIEW API
# ============================================================

class Api:


    def minimize(self):

        try:

            if webview.windows:

                webview.windows[0].minimize()

        except Exception:

            pass


    def close(self):

        try:

            if webview.windows:

                webview.windows[0].destroy()

        except Exception:

            pass


# ============================================================
# MAIN
# ============================================================

def main():

    application_start = time.time()


    try:

        # ----------------------------------------------------
        # START LOG
        # ----------------------------------------------------

        write_log(
            ""
        )

        write_log(
            "================================"
        )

        write_log(
            "START APPLICATION"
        )

        write_log(
            "================================"
        )


        write_log(
            f"EXE_DIR = {EXE_DIR}"
        )


        write_log(
            f"BUNDLE_DIR = {BUNDLE_DIR}"
        )


        write_log(
            f"BASE_DIR = {BASE_DIR}"
        )


        write_log(
            f"IS_FROZEN = {IS_FROZEN}"
        )


        write_log(
            f"PORT = {PORT}"
        )


        # ----------------------------------------------------
        # PROXY
        # ----------------------------------------------------

        write_log(
            f"NO_PROXY = "
            f"{os.environ.get('NO_PROXY')}"
        )


        # ----------------------------------------------------
        # DIRECTORIES
        # ----------------------------------------------------

        prepare_directories()


        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        if not prepare_database():

            write_log(
                "WARNING: DATABASE PREPARATION FAILED"
            )


        # ----------------------------------------------------
        # MEDIA
        # ----------------------------------------------------

        if not prepare_media_images():

            write_log(
                "WARNING: MEDIA PREPARATION FAILED"
            )


        # ----------------------------------------------------
        # WKHTMLTOPDF
        # ----------------------------------------------------

        check_wkhtmltopdf()


        # ----------------------------------------------------
        # BACKUP
        # ----------------------------------------------------

        backup_database()


        # ----------------------------------------------------
        # START DJANGO THREAD
        # ----------------------------------------------------

        write_log(
            "CREATING DJANGO THREAD"
        )


        django_thread = threading.Thread(

            target=start_django,

            daemon=True

        )


        django_thread.start()


        write_log(
            "DJANGO THREAD STARTED"
        )


        # ----------------------------------------------------
        # WAIT FOR DJANGO
        # ----------------------------------------------------

        if not wait_for_django():

            write_log(
                "DJANGO DID NOT START"
            )


            return


        # ----------------------------------------------------
        # WEBVIEW
        # ----------------------------------------------------

        webview_start_time = time.time()


        write_log(
            "CREATING WEBVIEW WINDOW"
        )


        window = webview.create_window(

            APP_NAME,

            f"http://127.0.0.1:{PORT}/",

            width=1400,

            height=900,

            resizable=True,

            text_select=True,

            js_api=Api(),

        )


        write_log(
            "WEBVIEW WINDOW CREATED"
        )


        write_log(
            "STARTING WEBVIEW"
        )


        # ----------------------------------------------------
        # تشغيل WebView
        # ----------------------------------------------------

        webview.start()


        webview_elapsed = (
            time.time()
            - webview_start_time
        )


        write_log(
            f"WEBVIEW ENDED "
            f"AFTER {webview_elapsed:.2f} SEC"
        )


    except Exception:

        write_log(
            "================================"
        )

        write_log(
            "FATAL ERROR"
        )

        write_log(
            traceback.format_exc()
        )


    finally:

        application_elapsed = (
            time.time()
            - application_start
        )


        write_log(
            "================================"
        )

        write_log(
            f"APPLICATION ENDED "
            f"AFTER {application_elapsed:.2f} SEC"
        )

        write_log(
            "================================"
        )


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    main()