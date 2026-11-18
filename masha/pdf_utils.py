# -*- coding: utf-8 -*-

import os
import re
import base64
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings


# ============================================================
# قراءة الصورة وتحويلها إلى Base64
# ============================================================

def get_image_base64(image_name):

    try:

        image_path = (
            Path(settings.STATIC_SOURCE_DIR)
            / "assets"
            / "image"
            / image_name
        )

        print("IMAGE PATH:")
        print(image_path)

        if not image_path.is_file():

            print(
                "IMAGE NOT FOUND:",
                image_path
            )

            return ""

        with open(
            image_path,
            "rb"
        ) as image_file:

            encoded = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        extension = image_path.suffix.lower()

        mime_types = {

            ".jpg": "image/jpeg",

            ".jpeg": "image/jpeg",

            ".png": "image/png",

            ".gif": "image/gif",

            ".webp": "image/webp",

        }

        mime = mime_types.get(
            extension,
            "image/jpeg"
        )

        return (
            f"data:{mime};base64,{encoded}"
        )

    except Exception as e:

        print(
            "IMAGE BASE64 ERROR:",
            e
        )

        return ""


# ============================================================
# تنظيف اسم الملف
# ============================================================

def clean_filename(name):

    name = str(name)

    name = re.sub(
        r'[\\/:*?"<>|]+',
        "_",
        name
    )

    name = name.strip()

    if not name:

        name = "report"

    return name


# ============================================================
# تحديد Downloads
# ============================================================

def get_downloads_folder():

    home = Path.home()

    downloads = (
        home / "Downloads"
    )

    # ========================================================
    # بعض أجهزة Windows تستخدم اسمًا عربيًا أو مسارًا مختلفًا
    # ========================================================

    if downloads.exists():

        return downloads

    # ========================================================
    # إنشاء Downloads إذا لم يكن موجودًا
    # ========================================================

    try:

        downloads.mkdir(
            parents=True,
            exist_ok=True
        )

        return downloads

    except Exception:

        return home


# ============================================================
# البحث عن wkhtmltopdf
# ============================================================

def get_wkhtmltopdf():

    candidates = []

    # ========================================================
    # من settings.py
    # ========================================================

    configured = getattr(
        settings,
        "WKHTMLTOPDF_CMD",
        None
    )

    if configured:

        candidates.append(
            Path(configured)
        )

    # ========================================================
    # BUNDLE_DIR
    # ========================================================

    bundle_dir = getattr(
        settings,
        "BUNDLE_DIR",
        None
    )

    if bundle_dir:

        candidates.append(

            Path(bundle_dir)
            / "wkhtmltopdf"
            / "bin"
            / "wkhtmltopdf.exe"

        )

    # ========================================================
    # APP_DIR
    # ========================================================

    app_dir = getattr(
        settings,
        "APP_DIR",
        None
    )

    if app_dir:

        candidates.append(

            Path(app_dir)
            / "wkhtmltopdf"
            / "bin"
            / "wkhtmltopdf.exe"

        )

    # ========================================================
    # المسارات القديمة للتطوير فقط
    # ========================================================

    candidates.append(

        Path(
            r"D:\erea\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )

    )

    candidates.append(

        Path(
            r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )

    )

    # ========================================================
    # البحث
    # ========================================================

    for path in candidates:

        try:

            if path.is_file():

                print(
                    "WKHTMLTOPDF:",
                    path
                )

                return str(path)

        except Exception:

            pass

    return None


# ============================================================
# إنشاء PDF وحفظه في Downloads
# ============================================================

def save_pdf_to_downloads(
    html,
    person_name,
    report_name="تقرير"
):

    # ========================================================
    # wkhtmltopdf
    # ========================================================

    wkhtmltopdf = get_wkhtmltopdf()

    if not wkhtmltopdf:

        raise RuntimeError(
            "لم يتم العثور على wkhtmltopdf.exe"
        )

    # ========================================================
    # Downloads
    # ========================================================

    downloads = get_downloads_folder()

    # ========================================================
    # اسم الملف
    # ========================================================

    person_name = clean_filename(
        person_name
    )

    report_name = clean_filename(
        report_name
    )

    filename = (
        f"{report_name}_{person_name}.pdf"
    )

    output_file = (
        downloads / filename
    )

    # ========================================================
    # إذا كان الملف موجودًا
    # ========================================================

    if output_file.exists():

        try:

            output_file.unlink()

        except Exception:

            pass

    # ========================================================
    # HTML مؤقت
    # ========================================================

    temp_html = None

    try:

        with tempfile.NamedTemporaryFile(

            mode="w",

            encoding="utf-8",

            suffix=".html",

            delete=False

        ) as html_file:

            html_file.write(
                html
            )

            temp_html = html_file.name

        # ====================================================
        # خيارات wkhtmltopdf
        # ====================================================

        command = [

            wkhtmltopdf,

            "--page-size",
            "A4",

            "--orientation",
            "Portrait",

            "--encoding",
            "UTF-8",

            "--enable-local-file-access",

            "--margin-top",
            "0",

            "--margin-bottom",
            "0",

            "--margin-left",
            "0",

            "--margin-right",
            "0",

            "--disable-smart-shrinking",

            "--no-stop-slow-scripts",

            temp_html,

            str(output_file),

        ]

        print(
            "RUN WKHTMLTOPDF:"
        )

        print(
            command
        )

        # ====================================================
        # تشغيل wkhtmltopdf
        # ====================================================

        result = subprocess.run(

            command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            encoding="utf-8",

            errors="replace"

        )

        # ====================================================
        # فحص النتيجة
        # ====================================================

        if result.returncode != 0:

            raise RuntimeError(

                "فشل إنشاء PDF:\n"

                + result.stderr

            )

        # ====================================================
        # التأكد من وجود PDF
        # ====================================================

        if not output_file.exists():

            raise RuntimeError(
                "تم تشغيل wkhtmltopdf ولكن ملف PDF لم يتم إنشاؤه."
            )

        # ====================================================
        # فتح PDF تلقائيًا
        # ====================================================

        try:

            os.startfile(
                str(output_file)
            )

        except Exception as e:

            print(
                "OPEN PDF ERROR:",
                e
            )

        # ====================================================
        # إرجاع المسار
        # ====================================================

        return str(
            output_file
        )

    finally:

        # ====================================================
        # حذف HTML المؤقت
        # ====================================================

        if temp_html:

            try:

                os.remove(
                    temp_html
                )

            except Exception:

                pass