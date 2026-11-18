# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
)


# ============================================================
# PROJECT
# ============================================================

PROJECT = r"D:\erea"

DESKTOP = os.path.join(
    PROJECT,
    "desktop_django.py"
)


# ============================================================
# HELPERS
# ============================================================

datas = []

binaries = []


def add_data(
    source,
    destination
):

    if os.path.exists(source):

        datas.append(
            (
                source,
                destination
            )
        )


# ============================================================
# TEMPLATES
# ============================================================

add_data(

    os.path.join(
        PROJECT,
        "templates"
    ),

    "templates"

)


add_data(

    os.path.join(
        PROJECT,
        "accounts",
        "templates"
    ),

    os.path.join(
        "accounts",
        "templates"
    )

)


add_data(

    os.path.join(
        PROJECT,
        "masha",
        "templates"
    ),

    os.path.join(
        "masha",
        "templates"
    )

)


# ============================================================
# STATIC SOURCE
# ============================================================

add_data(

    os.path.join(
        PROJECT,
        "static_source"
    ),

    "static_source"

)


# ============================================================
# FONTS
# ============================================================

FONTS = os.path.join(
    PROJECT,
    "fonts"
)

if os.path.isdir(FONTS):

    add_data(
        FONTS,
        "fonts"
    )


# ============================================================
# MEDIA IMAGES
#
# مهم جدًا
# ============================================================

MEDIA_IMAGES = os.path.join(

    PROJECT,
    "media",
    "images"

)

if os.path.isdir(
    MEDIA_IMAGES
):

    add_data(

        MEDIA_IMAGES,

        os.path.join(
            "media",
            "images"
        )

    )


# ============================================================
# DATABASE INITIAL
# ============================================================

DB_FILE = os.path.join(

    PROJECT,
    "db.sqlite3"

)

if os.path.isfile(
    DB_FILE
):

    add_data(
        DB_FILE,
        "."
    )


# ============================================================
# WKHTMLTOPDF
# ============================================================

WKHTML_DIR = os.path.join(

    PROJECT,
    "wkhtmltopdf"

)


if os.path.isdir(
    WKHTML_DIR
):

    for root, dirs, files in os.walk(
        WKHTML_DIR
    ):

        relative = os.path.relpath(
            root,
            WKHTML_DIR
        )

        destination = os.path.join(

            "wkhtmltopdf",

            ""
            if relative == "."
            else relative

        )

        for filename in files:

            source = os.path.join(
                root,
                filename
            )

            datas.append(
                (
                    source,
                    destination
                )
            )


# ============================================================
# REPORTLAB DATA
# ============================================================

try:

    datas += collect_data_files(
        "reportlab"
    )

except Exception:

    pass


# ============================================================
# WEBVIEW DATA
# ============================================================

try:

    datas += collect_data_files(
        "webview"
    )

except Exception:

    pass


# ============================================================
# HIDDEN IMPORTS
# ============================================================

hiddenimports = []


hiddenimports += collect_submodules(
    "django"
)

hiddenimports += collect_submodules(
    "erea"
)

hiddenimports += collect_submodules(
    "masha"
)

hiddenimports += collect_submodules(
    "accounts"
)

hiddenimports += collect_submodules(
    "bootstrap4"
)

hiddenimports += collect_submodules(
    "import_export"
)

hiddenimports += collect_submodules(
    "reportlab"
)

hiddenimports += collect_submodules(
    "webview"
)

hiddenimports += collect_submodules(
    "django_auto_logout"
)

hiddenimports += collect_submodules(
    "dbbackup"
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def unique_items(items):

    result = []

    seen = set()

    for item in items:

        key = (
            str(item).lower()
        )

        if key in seen:

            continue

        seen.add(key)

        result.append(item)

    return result


datas = unique_items(
    datas
)

binaries = unique_items(
    binaries
)

hiddenimports = unique_items(
    hiddenimports
)


# ============================================================
# ANALYSIS
# ============================================================

a = Analysis(

    [DESKTOP],

    pathex=[
        PROJECT
    ],

    binaries=binaries,

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,

)


# ============================================================
# PYZ
# ============================================================

pyz = PYZ(

    a.pure,

    a.zipped_data,

)


# ============================================================
# EXE
# ============================================================

exe = EXE(

    pyz,

    a.scripts,

    a.binaries,

    a.datas,

    [],

    name="نظام_المساحة",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    console=False,

)
