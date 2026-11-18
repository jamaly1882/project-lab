# -*- coding: utf-8 -*-

"""
Django settings for erea project.
"""

import os
import sys
import logging
from pathlib import Path


# ============================================================
# BASIC
# ============================================================

BASE_SOURCE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# هل البرنامج يعمل كـ EXE؟
# ============================================================

IS_FROZEN = bool(
    getattr(sys, "frozen", False)
)


# ============================================================
# APP DIRECTORY
#
# أثناء التطوير:
# D:\erea
#
# أثناء EXE:
# المجلد الذي يوجد فيه نظام_المساحة.exe
# ============================================================

if IS_FROZEN:

    APP_DIR = Path(
        os.path.abspath(
            os.path.dirname(
                sys.executable
            )
        )
    )

else:

    APP_DIR = BASE_SOURCE_DIR


# ============================================================
# PYINSTALLER BUNDLE DIRECTORY
#
# EXE:
# _MEIPASS
#
# التطوير:
# D:\erea
# ============================================================

if IS_FROZEN:

    BUNDLE_DIR = Path(
        getattr(
            sys,
            "_MEIPASS",
            APP_DIR
        )
    )

else:

    BUNDLE_DIR = BASE_SOURCE_DIR


# ============================================================
# BASE_DIR
# ============================================================

BASE_DIR = APP_DIR


# ============================================================
# SECRET KEY
# ============================================================

SECRET_KEY = (
    "django-insecure-change-this-key"
)


# ============================================================
# DEBUG
# ============================================================

DEBUG = False


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "masha",
    "accounts",

]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",

]


# ============================================================
# ROOT URL
# ============================================================

ROOT_URLCONF = "erea.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [

    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {

            "context_processors": [

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

            ],

        },

    },

]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "erea.wsgi.application"


# ============================================================
# DATABASE
#
# قاعدة البيانات الخارجية بجانب EXE
# ============================================================

DATABASE_PATH = (
    APP_DIR / "db.sqlite3"
)


DATABASES = {

    "default": {

        "ENGINE":
            "django.db.backends.sqlite3",

        "NAME":
            str(DATABASE_PATH),

    }

}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = []


# ============================================================
# LANGUAGE
# ============================================================

LANGUAGE_CODE = "ar"

TIME_ZONE = "Asia/Aden"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC
# ============================================================

STATIC_URL = "/static/"


# ============================================================
# static_source
#
# ملفات static الأصلية داخل PyInstaller
# ============================================================

STATIC_SOURCE_DIR = (
    BUNDLE_DIR / "static_source"
)


# ============================================================
# static
#
# مجلد خارجي قابل للكتابة بجانب EXE
# ============================================================

STATIC_ROOT = (
    APP_DIR / "static"
)


# ============================================================
# مهم جدًا:
#
# لا نضع STATIC_ROOT داخل STATICFILES_DIRS
# ============================================================

STATICFILES_DIRS = []


if STATIC_SOURCE_DIR.is_dir():

    STATICFILES_DIRS.append(
        STATIC_SOURCE_DIR
    )


# ============================================================
# MEDIA
#
# الصور التي يرفعها المستخدم تحفظ بجانب EXE
# ============================================================

MEDIA_URL = "/media/"


MEDIA_ROOT = (
    APP_DIR / "media"
)


# ============================================================
# DIRECTORIES
# ============================================================

BACKUP_DIR = (
    APP_DIR / "backup"
)

SESSION_DIR = (
    APP_DIR / "session"
)

LOG_DIR = (
    APP_DIR / "logs"
)

FONTS_DIR = (
    BUNDLE_DIR / "fonts"
)


# ============================================================
# إنشاء المجلدات
# ============================================================

for directory in [

    APP_DIR,

    MEDIA_ROOT,

    BACKUP_DIR,

    SESSION_DIR,

    LOG_DIR,

    STATIC_ROOT,

]:

    try:

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

    except Exception:
        pass


# ============================================================
# SESSIONS
# ============================================================

SESSION_ENGINE = (
    "django.contrib.sessions.backends.file"
)

SESSION_FILE_PATH = str(
    SESSION_DIR
)


# ============================================================
# STATIC FILES
# ============================================================

STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)


# ============================================================
# DEFAULT AUTO FIELD
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ============================================================
# WKHTMLTOPDF
# ============================================================

WKHTMLTOPDF_CANDIDATES = [

    BUNDLE_DIR
    / "wkhtmltopdf"
    / "bin"
    / "wkhtmltopdf.exe",

    APP_DIR
    / "wkhtmltopdf"
    / "bin"
    / "wkhtmltopdf.exe",

    BASE_SOURCE_DIR
    / "wkhtmltopdf"
    / "bin"
    / "wkhtmltopdf.exe",

    Path(
        r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe"
    ),

]


# ============================================================
# LOGGING
# ============================================================

LOG_FILE = (
    LOG_DIR / "erea.log"
)


LOGGING = {

    "version": 1,

    "disable_existing_loggers": False,

    "formatters": {

        "verbose": {

            "format":
                "[{asctime}] "
                "{levelname} "
                "{name}: "
                "{message}",

            "style": "{",

        },

    },

    "handlers": {

        "file": {

            "level": "INFO",

            "class":
                "logging.FileHandler",

            "filename":
                str(LOG_FILE),

            "encoding":
                "utf-8",

            "formatter":
                "verbose",

        },

        "console": {

            "level": "INFO",

            "class":
                "logging.StreamHandler",

            "formatter":
                "verbose",

        },

    },

    "loggers": {

        "django": {

            "handlers": [
                "file",
                "console",
            ],

            "level": "INFO",

            "propagate": False,

        },

        "erea": {

            "handlers": [
                "file",
                "console",
            ],

            "level": "INFO",

            "propagate": False,

        },

    },

}


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]