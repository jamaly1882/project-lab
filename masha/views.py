from django.shortcuts import render, redirect,reverse

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from requests.exceptions import RequestException
from django.contrib import messages
from .models import report_masahi
from datetime import datetime
from django.utils import timezone
from zoneinfo import ZoneInfo

# Activate Riyadh timezone for the request/thread
timezone.activate(ZoneInfo("Asia/Riyadh"))

# Get current time in Riyadh
current_datetime = timezone.now()
import sys
# Create your views here.
from .models import Mahfth,Erea,Gata,Unit,Eng,typ,Form,Safah,AStmrah,Typ_bana,Vald_doc,Eng_nazol,Resone,Shift_form_hadod,report_masahi,Streat,Location,Mahther_line,Shift_streatr,Conection,Location_Utm,Type_map,Valdtion,Type_block,Type_natural,Type_seol,Type_kah,Type_talb,Type_talb_astshr,Vald_tharb
from .scoping import (
    filter_forms,
    filter_reports,
    get_user_mahfth,
    resolve_mahfth_for_user,
    visible_mahfth_list,
)
from django.contrib import messages
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth import authenticate,login
from .forms import Shift_form_hadodForm,Shift_streatrForm,Location_UtmForm,verificationForm,EngNazolForm,BaseShiftFormSet

from django.forms.formsets import formset_factory
import time
import random
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Type_natural
from .forms import TypeNaturalForm
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Type_natural
from .forms import TypeNaturalForm
import json
import time
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import typ
from .forms import TypForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Type_block, Type_natural
from .forms import TypeBlockForm, TypeNaturalForm
from datetime import datetime
import pytz
timezone = pytz.timezone('Asia/Riyadh')
current_datetime = datetime.now(timezone)
from django.core import serializers
from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required ,permission_required
from django.contrib.auth.decorators import user_passes_test as _user_passes_test


# ============================================================
# صلاحيات الوصول المبنية على المدينة / المديرية
#
# * مدير النظام (superuser / staff) يصل لكل شيء.
# * المستخدم العادي يصل لأقسام مدينته/مديريته فقط، دون الحاجة إلى
#   صلاحية Django خاصة — لأن نطاق البيانات مقيّد أصلاً في scoping.py.
# ============================================================


def _user_in_scope(user):
    """هل المستخدم مرتبط بمدينة أو مديرية؟"""
    if user is None or not getattr(user, "is_authenticated", False):
        return False

    from .scoping import get_user_city_name, get_user_mahfth

    return bool(get_user_mahfth(user) or get_user_city_name(user))


def is_manager(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (user.is_superuser or user.is_staff)
    )


SPACE_ROLE_HEAD = "رئيس قسم مساحة"
SPACE_ROLE_ENGINEER = "مهندس مساحة"
SPACE_ROLE_COORDINATOR = "منسق قسم مساحة"
SPACE_ROLE_AREA_MANAGER = "مدير إدارة المساحة"
SPACE_ROLES = {SPACE_ROLE_HEAD, SPACE_ROLE_ENGINEER, SPACE_ROLE_COORDINATOR}


def get_space_role(user):
    """الدور المساحي المختار للمستخدم من لوحة إدارة المستخدمين."""
    try:
        return user.profile.role
    except Exception:
        return ""


def role_landing_url(user):
    """صفحة الدخول المباشرة لكل دور بدلاً من عرض أيقونة اختيار الدور."""
    if is_manager(user):
        return None
    return {
        SPACE_ROLE_HEAD: "masha:show_manager_masah_nah",
        SPACE_ROLE_ENGINEER: "masha:show_astmrat",
        SPACE_ROLE_COORDINATOR: "masha:interface",
        SPACE_ROLE_AREA_MANAGER: "masha:screen_adrat_ver",
    }.get(get_space_role(user))


def space_roles_only(allowed_roles=None, block_management=False):
    """حماية روابط الأيقونات؛ المديرون والحسابات القديمة تظل على سلوكها المعتاد."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            role = get_space_role(user)
            if role in SPACE_ROLES and not is_manager(user):
                if block_management or (allowed_roles and role not in allowed_roles):
                    messages.warning(request, "لا تملك صلاحية الدخول إلى هذه الأيقونة.")
                    return redirect(role_landing_url(user) or "masha:screen_paesdint_masah")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def coordinator_or_manager_required(view_func):
    """السماح بإصدار التقارير للمنسق ومدير النظام فقط."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return redirect_to_login(request.get_full_path(), "accounts:login")
        if is_manager(user) or get_space_role(user) == SPACE_ROLE_COORDINATOR:
            return view_func(request, *args, **kwargs)

        messages.warning(request, "إصدار التقارير متاح لمنسق القسم ومدير النظام فقط.")
        role = get_space_role(user)
        if role == SPACE_ROLE_HEAD:
            return redirect("masha:show_manager_masah_nah")
        if role == SPACE_ROLE_ENGINEER:
            return redirect("masha:show_astmrat")
        return redirect("masha:index")
    return _wrapped


def can_access_mahfth_screen(user):
    """الوصول إلى شاشات الأقسام وفق المديريات أو الدور الإداري العام."""
    return (
        is_manager(user)
        or get_space_role(user) == SPACE_ROLE_AREA_MANAGER
        or _user_in_scope(user)
    )


def mahfth_screen_required(view_func):
    """بديل permission_required لشاشات الأقسام المقيّدة بالمدينة/المديرية.

    * غير مسجّل الدخول      → صفحة الدخول مع next.
    * مسجّل بدون مدينة/مديرية → لوحة التحكم مع رسالة توضيحية.
    * أو مستخدم مرتبط بمدينة/مديرية → يُسمح له.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), "accounts:login")

        if not can_access_mahfth_screen(request.user):
            messages.warning(
                request,
                "لم يتم ربط حسابك بأي مدينة أو مديرية بعد، "
                "يرجى مراجعة مدير النظام لتفعيل الوصول إلى الأقسام.",
            )
            return redirect("masha:index")

        return view_func(request, *args, **kwargs)

    return _wrapped

import folium
from folium.plugins import FastMarkerCluster
from folium.plugins import MiniMap
import pdfkit
from django.shortcuts import render, redirect
from .models import Type_map
from .forms import TypeMapForm
from django.http import FileResponse
from django.template import Context
import pdfkit

from django.http import FileResponse
from xhtml2pdf import pisa
from django.contrib.auth.models  import User
from django.template.loader import get_template
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt 
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Type_talb_astshr
from .forms import TypeTalbAstshrForm
import os
import base64
import mimetypes
import pdfkit

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template

from .models import Form
import os
import base64
import mimetypes
import pdfkit

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template

from .models import Form


# ============================================================

import os
import sys
import base64
import mimetypes
import pdfkit

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template

import os
import sys
import base64
import mimetypes
import logging
import tempfile
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

import pdfkit


logger = logging.getLogger(__name__)
# ============================================================
# تحويل الصورة إلى Base64
# ============================================================



# ============================================================
# IMPORTS
# ============================================================

import os
import sys
import base64
import mimetypes
import pdfkit

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template

import os
import sys
import base64
import mimetypes

from urllib.parse import quote
# ============================================================
# المسار الأساسي للتطبيق
# ============================================================

# ============================================================
# APP DIRECTORY
# ============================================================

def get_app_dir():

    try:

        if getattr(sys, "frozen", False):

            return os.path.dirname(
                os.path.abspath(
                    sys.executable
                )
            )

        return str(
            settings.BASE_DIR
        )

    except Exception:

        logger.exception(
            "ERROR IN get_app_dir"
        )

        return os.getcwd()


# ============================================================
# PYINSTALLER BUNDLE DIRECTORY
# ============================================================

def get_bundle_dir():

    try:

        if getattr(sys, "frozen", False):

            return getattr(
                sys,
                "_MEIPASS",
                os.path.dirname(
                    os.path.abspath(
                        sys.executable
                    )
                )
            )

        return str(
            settings.BASE_DIR
        )

    except Exception:

        logger.exception(
            "ERROR IN get_bundle_dir"
        )

        return os.getcwd()


# ============================================================
# FIND FILE
# ============================================================

def find_existing_file(candidates):

    try:

        for candidate in candidates:

            if not candidate:
                continue

            path = Path(candidate)

            if path.is_file():

                logger.info(
                    "FILE FOUND: %s",
                    path
                )

                return str(path)

        logger.warning(
            "FILE NOT FOUND"
        )

        for candidate in candidates:

            logger.warning(
                "CANDIDATE: %s",
                candidate
            )

        return None

    except Exception:

        logger.exception(
            "ERROR IN find_existing_file"
        )

        return None


# ============================================================
# FIND DIRECTORY
# ============================================================

def find_existing_dir(candidates):

    try:

        for candidate in candidates:

            if not candidate:
                continue

            path = Path(candidate)

            if path.is_dir():

                logger.info(
                    "DIRECTORY FOUND: %s",
                    path
                )

                return str(path)

        logger.warning(
            "DIRECTORY NOT FOUND"
        )

        for candidate in candidates:

            logger.warning(
                "DIRECTORY CANDIDATE: %s",
                candidate
            )

        return None

    except Exception:

        logger.exception(
            "ERROR IN find_existing_dir"
        )

        return None
# ============================================================
# مسار PyInstaller الداخلي
# ============================================================



# ============================================================
# البحث عن ملف
# ============================================================


# ============================================================
# البحث عن مجلد
# ============================================================




# ============================================================
# الصورة
# ============================================================

# ============================================================
# REPORT HEADER IMAGE
# ============================================================

def get_report_image_path():

    try:

        app_dir = Path(
            get_app_dir()
        )

        bundle_dir = Path(
            get_bundle_dir()
        )

        base_dir = Path(
            settings.BASE_DIR
        )

        candidates = [

            app_dir
            / "static_source"
            / "assets"
            / "image"
            / "bg-head.jpg",

            bundle_dir
            / "static_source"
            / "assets"
            / "image"
            / "bg-head.jpg",

            app_dir
            / "static"
            / "assets"
            / "image"
            / "bg-head.jpg",

            base_dir
            / "static_source"
            / "assets"
            / "image"
            / "bg-head.jpg",

            base_dir
            / "static"
            / "assets"
            / "image"
            / "bg-head.jpg",
        ]

        return find_existing_file(
            candidates
        )

    except Exception:

        logger.exception(
            "ERROR IN get_report_image_path"
        )

        return None
# ============================================================
# تحويل صورة إلى Base64
# ============================================================

# ============================================================
# IMAGE TO BASE64
# ============================================================

def image_to_base64(image_path):

    try:

        if not image_path:

            logger.warning(
                "IMAGE PATH IS EMPTY"
            )

            return ""

        if not os.path.isfile(
            image_path
        ):

            logger.warning(
                "IMAGE NOT FOUND: %s",
                image_path
            )

            return ""

        with open(
            image_path,
            "rb"
        ) as image_file:

            encoded = base64.b64encode(
                image_file.read()
            ).decode(
                "utf-8"
            )

        mime_type, _ = mimetypes.guess_type(
            image_path
        )

        if not mime_type:

            mime_type = "image/jpeg"

        return (
            f"data:{mime_type};base64,"
            f"{encoded}"
        )

    except Exception:

        logger.exception(
            "ERROR IN image_to_base64"
        )

        return ""


# ============================================================
# مجلد الخطوط
# ============================================================

# ============================================================
# FONTS DIRECTORY
# ============================================================
def image_field_to_base64(image_field):
    """
    تحويل ImageField إلى Base64.

    تعمل في:
        - Django أثناء التطوير
        - نسخة EXE
        - PyInstaller

    تبحث عن الصورة بالترتيب:
        1. Django Storage
        2. MEDIA_ROOT
        3. مجلد التطبيق
        4. مجلد PyInstaller _MEIPASS
    """

    try:

        # ========================================================
        # 1. التحقق من ImageField
        # ========================================================

        if not image_field:

            logger.warning(
                "IMAGE FIELD IS EMPTY"
            )

            return ""

        # ========================================================
        # 2. اسم الصورة من ImageField
        # ========================================================

        image_name = str(
            getattr(
                image_field,
                "name",
                ""
            ) or ""
        ).strip()

        if not image_name:

            logger.warning(
                "IMAGE FIELD NAME IS EMPTY"
            )

            return ""

        # توحيد الفواصل
        image_name = image_name.replace(
            "\\",
            "/"
        )

        # إزالة / من البداية
        image_name = image_name.lstrip("/")

        logger.info(
            "IMAGE FIELD NAME: %s",
            image_name
        )

        # ========================================================
        # متغير لحفظ بيانات الصورة
        # ========================================================

        image_data = None

        # ========================================================
        # 3. محاولة Django Storage
        # ========================================================

        try:

            storage = image_field.storage

            logger.info(
                "IMAGE STORAGE TYPE: %s",
                type(storage).__name__
            )

            if storage.exists(
                image_name
            ):

                logger.info(
                    "IMAGE FOUND IN DJANGO STORAGE"
                )

                with storage.open(
                    image_name,
                    "rb"
                ) as image_file:

                    image_data = (
                        image_file.read()
                    )

                logger.info(
                    "IMAGE READ FROM STORAGE | bytes=%s",
                    len(image_data)
                )

            else:

                logger.warning(
                    "IMAGE NOT FOUND IN DJANGO STORAGE: %s",
                    image_name
                )

        except Exception:

            logger.exception(
                "ERROR READING IMAGE FROM DJANGO STORAGE"
            )

        # ========================================================
        # 4. البحث في MEDIA_ROOT
        # ========================================================

        if not image_data:

            try:

                media_root = Path(
                    settings.MEDIA_ROOT
                ).resolve()

                media_path = (
                    media_root /
                    image_name
                ).resolve()

                logger.info(
                    "MEDIA ROOT IMAGE PATH: %s",
                    media_path
                )

                if media_path.is_file():

                    logger.info(
                        "IMAGE FOUND IN MEDIA_ROOT"
                    )

                    with open(
                        media_path,
                        "rb"
                    ) as image_file:

                        image_data = (
                            image_file.read()
                        )

                    logger.info(
                        "IMAGE READ FROM MEDIA_ROOT | bytes=%s",
                        len(image_data)
                    )

                else:

                    logger.warning(
                        "IMAGE NOT FOUND IN MEDIA_ROOT"
                    )

            except Exception:

                logger.exception(
                    "ERROR READING IMAGE FROM MEDIA_ROOT"
                )

        # ========================================================
        # 5. البحث في مجلد التطبيق
        # ========================================================

        if not image_data:

            try:

                app_dir = Path(
                    get_app_dir()
                ).resolve()

                app_image_path = (
                    app_dir /
                    "media" /
                    image_name
                ).resolve()

                logger.info(
                    "APP MEDIA IMAGE PATH: %s",
                    app_image_path
                )

                if app_image_path.is_file():

                    logger.info(
                        "IMAGE FOUND IN APP MEDIA"
                    )

                    with open(
                        app_image_path,
                        "rb"
                    ) as image_file:

                        image_data = (
                            image_file.read()
                        )

                    logger.info(
                        "IMAGE READ FROM APP MEDIA | bytes=%s",
                        len(image_data)
                    )

                else:

                    logger.warning(
                        "IMAGE NOT FOUND IN APP MEDIA"
                    )

            except Exception:

                logger.exception(
                    "ERROR READING IMAGE FROM APP MEDIA"
                )

        # ========================================================
        # 6. البحث داخل PyInstaller _MEIPASS
        # ========================================================

        if not image_data:

            try:

                bundle_value = getattr(
                    sys,
                    "_MEIPASS",
                    None
                )

                if bundle_value:

                    bundle_dir = Path(
                        bundle_value
                    ).resolve()

                    bundle_image_path = (
                        bundle_dir /
                        "media" /
                        image_name
                    ).resolve()

                    logger.info(
                        "BUNDLE IMAGE PATH: %s",
                        bundle_image_path
                    )

                    if bundle_image_path.is_file():

                        logger.info(
                            "IMAGE FOUND IN _MEIPASS MEDIA"
                        )

                        with open(
                            bundle_image_path,
                            "rb"
                        ) as image_file:

                            image_data = (
                                image_file.read()
                            )

                        logger.info(
                            "IMAGE READ FROM _MEIPASS | bytes=%s",
                            len(image_data)
                        )

            except Exception:

                logger.exception(
                    "ERROR READING IMAGE FROM _MEIPASS"
                )

        # ========================================================
        # 7. لم يتم العثور على الصورة
        # ========================================================

        if not image_data:

            logger.error(
                "IMAGE NOT FOUND ANYWHERE: %s",
                image_name
            )

            return ""

        # ========================================================
        # 8. تحديد MIME TYPE
        # ========================================================

        mime_type, _ = (
            mimetypes.guess_type(
                image_name
            )
        )

        if not mime_type:

            extension = (
                Path(
                    image_name
                )
                .suffix
                .lower()
            )

            mime_types = {

                ".jpg":
                    "image/jpeg",

                ".jpeg":
                    "image/jpeg",

                ".png":
                    "image/png",

                ".gif":
                    "image/gif",

                ".webp":
                    "image/webp",

                ".bmp":
                    "image/bmp",

            }

            mime_type = mime_types.get(
                extension,
                "application/octet-stream"
            )

        logger.info(
            "IMAGE MIME TYPE: %s",
            mime_type
        )

        # ========================================================
        # 9. تحويل إلى Base64
        # ========================================================

        encoded = (
            base64.b64encode(
                image_data
            )
            .decode(
                "ascii"
            )
        )

        # ========================================================
        # 10. إنشاء Data URI
        # ========================================================

        result = (
            f"data:{mime_type};base64,{encoded}"
        )

        logger.info(
            "IMAGE BASE64 CREATED | "
            "name=%s | "
            "bytes=%s | "
            "base64_length=%s",
            image_name,
            len(image_data),
            len(result)
        )

        return result

    except Exception:

        logger.exception(
            "ERROR CONVERTING IMAGE FIELD TO BASE64"
        )

        return ""
def get_fonts_dir():

    try:

        app_dir = Path(
            get_app_dir()
        )

        bundle_dir = Path(
            get_bundle_dir()
        )

        base_dir = Path(
            settings.BASE_DIR
        )

        candidates = [

            app_dir / "fonts",

            bundle_dir / "fonts",

            base_dir / "fonts",

            Path(
                r"D:\erea\fonts"
            ),
        ]

        return find_existing_dir(
            candidates
        )

    except Exception:

        logger.exception(
            "ERROR IN get_fonts_dir"
        )

        return None


# ============================================================
# FONT FILE
# ============================================================

def get_font_path(font_name):

    try:

        fonts_dir = get_fonts_dir()

        if not fonts_dir:

            return None

        return find_existing_file([
            Path(fonts_dir) / font_name
        ])

    except Exception:

        logger.exception(
            "ERROR IN get_font_path"
        )

        return None


# ============================================================
# REPORT FONTS CSS
# ============================================================

def get_report_fonts_css():

    try:

        fonts_dir = get_fonts_dir()

        if not fonts_dir:

            logger.warning(
                "FONTS DIRECTORY NOT FOUND"
            )

            return ""

        fonts = [

            (
                "NotoKufiArabic",
                "NotoKufiArabic-Regular.ttf",
                "normal"
            ),

          
        ]

        css_parts = []

        for family, filename, weight in fonts:

            font_path = Path(
                fonts_dir
            ) / filename

            if not font_path.is_file():

                logger.warning(
                    "FONT NOT FOUND: %s",
                    font_path
                )

                continue

            font_url = (
                font_path
                .resolve()
                .as_uri()
            )

            css_parts.append(
                f"""
                @font-face {{
                    font-family: '{family}';
                    src: url('{font_url}');
                    font-weight: {weight};
                    font-style: normal;
                }}
                """
            )

        css = "\n".join(
            css_parts
        )

        logger.info(
            "REPORT FONTS CSS CREATED"
        )

        return css

    except Exception:

        logger.exception(
            "ERROR IN get_report_fonts_css"
        )

        return ""
# ============================================================
# إضافة الخطوط إلى HTML
# ============================================================

# ============================================================
# إضافة الخطوط إلى HTML
# ============================================================

def prepare_report_html(html):

    if html is None:

        html = ""

    html = str(
        html
    )

    fonts_css = get_report_fonts_css()

    font_style = f"""
    <style>

    {fonts_css}

    html,
    body {{

        font-family:
            "Arial",
            sans-serif;

        direction:
            lft;

        unicode-bidi:
            embed;

    }}

    </style>
    """

    charset = """
    <meta charset="UTF-8">
    """

    lower_html = html.lower()

    if "</head>" in lower_html:

        position = lower_html.find(
            "</head>"
        )

        html = (

            html[:position]

            +

            charset

            +

            font_style

            +

            html[position:]

        )

    else:

        html = (

            charset

            +

            font_style

            +

            html

        )

    return html

# ============================================================
# wkhtmltopdf
# ============================================================

# ============================================================
# WKHTMLTOPDF PATH
# ============================================================

# ============================================================
# الحصول على مسار wkhtmltopdf
# ============================================================

# ============================================================
# WKHTMLTOPDF PATH
# ============================================================

def get_wkhtmltopdf_path():

    try:

        app_dir = Path(
            get_app_dir()
        ).resolve()

        bundle_dir = Path(
            get_bundle_dir()
        ).resolve()

        base_dir = Path(
            settings.BASE_DIR
        ).resolve()

        candidates = [

            # ---------------------------------------------
            # 1. بجانب EXE
            # ---------------------------------------------

            app_dir
            / "wkhtmltopdf"
            / "bin"
            / "wkhtmltopdf.exe",


            # ---------------------------------------------
            # 2. داخل _MEIPASS
            # ---------------------------------------------

            bundle_dir
            / "wkhtmltopdf"
            / "bin"
            / "wkhtmltopdf.exe",


            # ---------------------------------------------
            # 3. أثناء التطوير
            # ---------------------------------------------

            base_dir
            / "wkhtmltopdf"
            / "bin"
            / "wkhtmltopdf.exe",


            # ---------------------------------------------
            # 4. تثبيت Windows
            # ---------------------------------------------

            Path(
                r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe"
            ),

        ]

        seen = set()

        for candidate in candidates:

            candidate = Path(
                candidate
            )

            key = os.path.normcase(
                os.path.abspath(
                    str(candidate)
                )
            )

            if key in seen:

                continue

            seen.add(key)

            logger.info(
                "CHECK WKHTMLTOPDF: %s",
                candidate
            )

            if candidate.is_file():

                bin_dir = (
                    candidate.parent
                )

                current_path = (
                    os.environ.get(
                        "PATH",
                        ""
                    )
                )

                if str(bin_dir) not in (
                    current_path.split(
                        os.pathsep
                    )
                ):

                    os.environ["PATH"] = (

                        str(bin_dir)

                        +

                        os.pathsep

                        +

                        current_path

                    )

                os.environ[
                    "WKHTMLTOPDF_CMD"
                ] = str(candidate)

                logger.info(
                    "WKHTMLTOPDF FOUND: %s",
                    candidate
                )

                return str(candidate)

        raise FileNotFoundError(
            "wkhtmltopdf.exe غير موجود"
        )

    except Exception:

        logger.exception(
            "ERROR IN get_wkhtmltopdf_path"
        )

        raise


# ============================================================
# تنظيف اسم PDF
# ============================================================

def clean_pdf_filename(
    filename
):

    try:

        filename = str(
            filename
        ).strip()

        if not filename:

            filename = "document.pdf"

        # ----------------------------------------------------
        # التأكد من الامتداد
        # ----------------------------------------------------

        if not filename.lower().endswith(
            ".pdf"
        ):

            filename += ".pdf"

        # ----------------------------------------------------
        # الأحرف الممنوعة في Windows
        # ----------------------------------------------------

        invalid_chars = '<>:"/\\|?*'

        for char in invalid_chars:

            filename = filename.replace(
                char,
                "_"
            )

        # ----------------------------------------------------
        # إزالة النقاط والمسافات من النهاية
        # ----------------------------------------------------

        filename = filename.rstrip(
            " ."
        )

        if not filename:

            filename = "document.pdf"

        return filename

    except Exception:

        logger.exception(
            "ERROR CLEANING PDF FILENAME"
        )

        return "document.pdf"
def clean_pdf_filename(filename):

    try:

        if not filename:

            filename = "document.pdf"

        filename = str(
            filename
        ).strip()

        invalid_chars = (
            '<>:"/\\|?*'
        )

        for char in invalid_chars:

            filename = filename.replace(
                char,
                "_"
            )

        filename = "".join(
            char
            for char in filename
            if ord(char) >= 32
        )

        if not filename.lower().endswith(
            ".pdf"
        ):

            filename += ".pdf"

        return filename

    except Exception:

        logger.exception(
            "ERROR IN clean_pdf_filename"
        )

        return "document.pdf"
# ============================================================
# مجلد Downloads
# ============================================================

# ============================================================
# DOWNLOADS DIRECTORY
# ============================================================

def get_downloads_dir():

    try:

        user_profile = os.environ.get(
            "USERPROFILE"
        )

        if user_profile:

            downloads = Path(
                user_profile
            ) / "Downloads"

        else:

            downloads = Path.home() / "Downloads"

        downloads.mkdir(
            parents=True,
            exist_ok=True
        )

        return str(
            downloads
        )

    except Exception:

        logger.exception(
            "ERROR IN get_downloads_dir"
        )

        fallback = Path.cwd() / "Downloads"

        fallback.mkdir(
            parents=True,
            exist_ok=True
        )

        return str(
            fallback
        )




# ============================================================
# CREATE PDF
# ============================================================

# ============================================================
# إنشاء PDF من HTML
# ============================================================

def create_pdf_from_html(
    html,
    pdf_path
):

    import os
    import subprocess
    import tempfile
    from pathlib import Path

    temp_pdf = None

    try:

        logger.info(
            "========== CREATE PDF =========="
        )

        # ====================================================
        # تحويل المسارات
        # ====================================================

        pdf_path = Path(
            pdf_path
        ).resolve()

        pdf_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        logger.info(
            "FINAL PDF PATH: %s",
            str(pdf_path)
        )

        # ====================================================
        # تجهيز HTML
        # ====================================================

        logger.info(
            "PREPARING REPORT HTML"
        )

        html = prepare_report_html(
            html
        )

        if not html:

            raise ValueError(
                "محتوى HTML فارغ"
            )

        if not isinstance(
            html,
            str
        ):

            raise TypeError(
                "HTML يجب أن يكون من نوع str"
            )

        logger.info(
            "HTML LENGTH: %s",
            len(html)
        )

        # ====================================================
        # البحث عن wkhtmltopdf
        # ====================================================

        logger.info(
            "SEARCHING FOR WKHTMLTOPDF"
        )

        wkhtmltopdf_path = (
            get_wkhtmltopdf_path()
        )

        logger.info(
            "WKHTMLTOPDF FOUND: %s",
            wkhtmltopdf_path
        )

        if not wkhtmltopdf_path:

            raise FileNotFoundError(
                "لم يتم العثور على wkhtmltopdf.exe"
            )

        wkhtmltopdf_path = str(
            Path(
                wkhtmltopdf_path
            ).resolve()
        )

        # ====================================================
        # التحقق من وجود wkhtmltopdf
        # ====================================================

        if not os.path.isfile(
            wkhtmltopdf_path
        ):

            raise FileNotFoundError(
                "ملف wkhtmltopdf.exe غير موجود:\n"
                + wkhtmltopdf_path
            )

        logger.info(
            "WKHTMLTOPDF FILE EXISTS"
        )

        # ====================================================
        # مجلد wkhtmltopdf
        # ====================================================

        wkhtmltopdf_bin = os.path.dirname(
            wkhtmltopdf_path
        )

        logger.info(
            "WKHTMLTOPDF BIN: %s",
            wkhtmltopdf_bin
        )

        # ====================================================
        # إضافة wkhtmltopdf إلى PATH
        # ====================================================

        current_path = os.environ.get(
            "PATH",
            ""
        )

        path_parts = [
            p
            for p in current_path.split(
                os.pathsep
            )
            if p
        ]

        wkhtmltopdf_bin_norm = (
            os.path.normcase(
                os.path.abspath(
                    wkhtmltopdf_bin
                )
            )
        )

        already_exists = any(

            os.path.normcase(
                os.path.abspath(
                    p
                )
            )
            == wkhtmltopdf_bin_norm

            for p in path_parts

        )

        if not already_exists:

            os.environ["PATH"] = (

                wkhtmltopdf_bin

                + os.pathsep

                + current_path

            )

        logger.info(
            "WKHTMLTOPDF PATH UPDATED"
        )

        # ====================================================
        # Environment
        # ====================================================

        os.environ[
            "WKHTMLTOPDF_CMD"
        ] = wkhtmltopdf_path

        os.environ[
            "PYTHONUTF8"
        ] = "1"

        os.environ[
            "PYTHONIOENCODING"
        ] = "utf-8"

        logger.info(
            "WKHTMLTOPDF_CMD: %s",
            os.environ.get(
                "WKHTMLTOPDF_CMD"
            )
        )

        # ====================================================
        # إنشاء ملف PDF مؤقت فريد
        # ====================================================

        fd, temp_name = tempfile.mkstemp(

            prefix="erea_report_",

            suffix=".pdf",

            dir=str(
                pdf_path.parent
            )

        )

        os.close(
            fd
        )

        temp_pdf = Path(
            temp_name
        )

        logger.info(
            "TEMP PDF: %s",
            str(temp_pdf)
        )

        # ====================================================
        # حذف الملف المؤقت الفارغ
        #
        # wkhtmltopdf سيعيد إنشاءه
        # ====================================================

        try:

            if temp_pdf.exists():

                temp_pdf.unlink()

        except Exception:

            pass

        # ====================================================
        # أمر wkhtmltopdf
        # ====================================================

        command = [

            wkhtmltopdf_path,

            # ------------------------------------------------
            # حجم الصفحة
            # ------------------------------------------------

            "--page-size",
            "A4",

            # ------------------------------------------------
            # الاتجاه
            # ------------------------------------------------

            "--orientation",
            "Portrait",

            # ------------------------------------------------
            # UTF-8
            # ------------------------------------------------

            "--encoding",
            "UTF-8",

            # ------------------------------------------------
            # السماح بالملفات المحلية
            # ------------------------------------------------

            "--enable-local-file-access",

            # ------------------------------------------------
            # JavaScript
            # ------------------------------------------------

            "--no-stop-slow-scripts",

            # ------------------------------------------------
            # تجاهل بعض أخطاء الموارد
            # ------------------------------------------------

            "--load-error-handling",
            "ignore",

            "--load-media-error-handling",
            "ignore",

            # ------------------------------------------------
            # الهوامش
            # ------------------------------------------------

            "--margin-top",
            "0",

            "--margin-bottom",
            "0",

            "--margin-left",
            "0",

            "--margin-right",
            "0",

            # ------------------------------------------------
            # نفس إعداد pdfkit السابق
            # ------------------------------------------------

            "--disable-smart-shrinking",

            # ------------------------------------------------
            # الإدخال من stdin
            # ------------------------------------------------

            "-",

            # ------------------------------------------------
            # PDF الناتج
            # ------------------------------------------------

            str(
                temp_pdf
            ),

        ]

        logger.info(
            "WKHTMLTOPDF COMMAND READY"
        )

        logger.info(
            "STARTING WKHTMLTOPDF DIRECTLY"
        )

        # ====================================================
        # Environment خاص بالعملية
        # ====================================================

        process_env = os.environ.copy()

        process_env[
            "PATH"
        ] = os.environ.get(
            "PATH",
            ""
        )

        process_env[
            "PYTHONUTF8"
        ] = "1"

        process_env[
            "PYTHONIOENCODING"
        ] = "utf-8"

        process_env[
            "WKHTMLTOPDF_CMD"
        ] = wkhtmltopdf_path

        # ====================================================
        # منع ظهور الشاشة السوداء في Windows
        # ====================================================

        startupinfo = None

        creationflags = 0

        if os.name == "nt":

            startupinfo = (
                subprocess.STARTUPINFO()
            )

            startupinfo.dwFlags |= (
                subprocess.STARTF_USESHOWWINDOW
            )

            startupinfo.wShowWindow = (
                subprocess.SW_HIDE
            )

            creationflags = (
                subprocess.CREATE_NO_WINDOW
            )

            logger.info(
                "WINDOWS HIDDEN CONSOLE ENABLED"
            )

        # ====================================================
        # تشغيل wkhtmltopdf
        # ====================================================

        process = subprocess.Popen(

            command,

            stdin=subprocess.PIPE,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            env=process_env,

            shell=False,

            startupinfo=startupinfo,

            creationflags=creationflags,

        )

        logger.info(
            "WKHTMLTOPDF PROCESS STARTED"
        )

        # ====================================================
        # تحويل HTML إلى UTF-8 bytes
        # ====================================================

        html_bytes = html.encode(
            "utf-8"
        )

        logger.info(
            "HTML UTF8 BYTES: %s",
            len(html_bytes)
        )

        # ====================================================
        # إرسال HTML إلى wkhtmltopdf
        # ====================================================

        stdout_data, stderr_data = (
            process.communicate(
                input=html_bytes
            )
        )

        # ====================================================
        # قراءة stdout
        # ====================================================

        try:

            stdout_text = (

                stdout_data.decode(
                    "utf-8",
                    errors="replace"
                )

                if stdout_data

                else ""

            )

        except Exception:

            stdout_text = ""

        # ====================================================
        # قراءة stderr
        # ====================================================

        try:

            stderr_text = (

                stderr_data.decode(
                    "utf-8",
                    errors="replace"
                )

                if stderr_data

                else ""

            )

        except Exception:

            stderr_text = ""

        # ====================================================
        # تسجيل stdout
        # ====================================================

        if stdout_text:

            logger.info(
                "WKHTMLTOPDF STDOUT:\n%s",
                stdout_text
            )

        # ====================================================
        # تسجيل stderr
        #
        # wkhtmltopdf يرسل Progress هنا غالبًا
        # ====================================================

        if stderr_text:

            logger.info(
                "WKHTMLTOPDF STDERR:\n%s",
                stderr_text
            )

        # ====================================================
        # كود الخروج
        # ====================================================

        return_code = (
            process.returncode
        )

        logger.info(
            "WKHTMLTOPDF RETURN CODE: %s",
            return_code
        )

        # ====================================================
        # التحقق من نجاح wkhtmltopdf
        # ====================================================

        if return_code != 0:

            error_message = (
                "wkhtmltopdf فشل في إنشاء PDF.\n"
                "Return Code: "
                + str(
                    return_code
                )
            )

            if stderr_text:

                error_message += (
                    "\nWKHTMLTOPDF STDERR:\n"
                    + stderr_text[-5000:]
                )

            raise RuntimeError(
                error_message
            )

        # ====================================================
        # التحقق من إنشاء الملف
        # ====================================================

        if not temp_pdf.exists():

            raise FileNotFoundError(

                "لم يتم إنشاء ملف PDF المؤقت:\n"

                + str(
                    temp_pdf
                )

            )

        # ====================================================
        # حجم الملف المؤقت
        # ====================================================

        temp_size = (
            temp_pdf.stat().st_size
        )

        logger.info(
            "TEMP PDF SIZE: %s",
            temp_size
        )

        if temp_size <= 0:

            raise ValueError(
                "ملف PDF المؤقت فارغ"
            )

        # ====================================================
        # نقل الملف إلى المسار النهائي
        # ====================================================

        logger.info(
            "MOVING TEMP PDF TO FINAL PATH"
        )

        os.replace(

            str(
                temp_pdf
            ),

            str(
                pdf_path
            )

        )

        # ====================================================
        # أصبح الملف المؤقت هو الملف النهائي
        # ====================================================

        temp_pdf = None

        # ====================================================
        # التحقق من الملف النهائي
        # ====================================================

        if not pdf_path.exists():

            raise FileNotFoundError(

                "لم يتم إنشاء ملف PDF النهائي:\n"

                + str(
                    pdf_path
                )

            )

        # ====================================================
        # حجم الملف النهائي
        # ====================================================

        final_size = (
            pdf_path.stat().st_size
        )

        logger.info(
            "FINAL PDF SIZE: %s",
            final_size
        )

        if final_size <= 0:

            raise ValueError(
                "ملف PDF النهائي فارغ"
            )

        # ====================================================
        # نجاح
        # ====================================================

        logger.info(
            "PDF CREATED SUCCESSFULLY"
        )

        logger.info(
            "PDF PATH: %s",
            str(pdf_path)
        )

        logger.info(
            "PDF SIZE: %s",
            final_size
        )

        logger.info(
            "========== CREATE PDF SUCCESS =========="
        )

        return str(
            pdf_path
        )

    except Exception:

        logger.exception(
            "========== CREATE PDF ERROR =========="
        )

        # ====================================================
        # حذف الملف المؤقت عند حدوث خطأ
        # ====================================================

        try:

            if (
                temp_pdf is not None
                and temp_pdf.exists()
            ):

                temp_pdf.unlink()

                logger.info(
                    "TEMP PDF DELETED"
                )

        except Exception:

            logger.exception(
                "ERROR DELETING TEMP PDF"
            )

        # ====================================================
        # إعادة الخطأ إلى generate_pdf_response
        # ====================================================

        raise
# ============================================================
# إنشاء Response للـ PDF
# ============================================================

def generate_pdf_response(
    html,
    pdf_filename,
    inline=True
):

    try:

        logger.info(
            "========== GENERATE PDF RESPONSE START =========="
        )

        # ====================================================
        # التحقق من HTML
        # ====================================================

        if html is None:
            raise ValueError(
                "HTML is None"
            )

        if not isinstance(html, str):
            raise TypeError(
                f"HTML must be str, got {type(html).__name__}"
            )

        logger.info(
            "HTML TYPE: %s",
            type(html).__name__
        )

        logger.info(
            "HTML LENGTH: %s",
            len(html)
        )

        # ====================================================
        # تنظيف اسم الملف
        # ====================================================

        pdf_filename = clean_pdf_filename(
            pdf_filename
        )

        logger.info(
            "PDF FILENAME: %s",
            pdf_filename
        )

        # ====================================================
        # مجلد Downloads
        # ====================================================

        downloads_dir = get_downloads_dir()

        downloads_dir = Path(
            downloads_dir
        )

        downloads_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        logger.info(
            "DOWNLOADS DIR: %s",
            str(downloads_dir)
        )

        # ====================================================
        # مسار PDF
        # ====================================================

        pdf_path = (
            downloads_dir
            / pdf_filename
        )

        logger.info(
            "PDF OUTPUT: %s",
            str(pdf_path)
        )

        # ====================================================
        # إنشاء PDF
        # ====================================================

        logger.info(
            "CALLING create_pdf_from_html()"
        )

        create_pdf_from_html(
            html,
            pdf_path
        )

        logger.info(
            "CREATE PDF FINISHED"
        )

        # ====================================================
        # التحقق من وجود الملف
        # ====================================================

        if not pdf_path.exists():

            raise FileNotFoundError(
                f"PDF file does not exist: {pdf_path}"
            )

        if not pdf_path.is_file():

            raise ValueError(
                f"PDF path is not a file: {pdf_path}"
            )

        # ====================================================
        # حجم الملف
        # ====================================================

        pdf_size = pdf_path.stat().st_size

        logger.info(
            "PDF SIZE ON DISK: %s",
            pdf_size
        )

        if pdf_size <= 0:

            raise ValueError(
                "PDF file is empty"
            )

        # ====================================================
        # قراءة PDF
        # ====================================================

        logger.info(
            "READING PDF FILE"
        )

        with open(
            pdf_path,
            "rb"
        ) as pdf_file:

            pdf_data = pdf_file.read()

        logger.info(
            "PDF DATA SIZE: %s",
            len(pdf_data)
        )

        if not pdf_data:

            raise ValueError(
                "PDF data is empty"
            )

        # ====================================================
        # إنشاء Response
        # ====================================================

        logger.info(
            "CREATING HttpResponse"
        )

        response = HttpResponse(
            pdf_data,
            content_type="application/pdf"
        )

        # ====================================================
        # inline / attachment
        # ====================================================

        disposition = (
            "inline"
            if inline
            else "attachment"
        )

        # ====================================================
        # اسم الملف UTF-8
        # ====================================================

        encoded_filename = quote(
            pdf_filename,
            safe=""
        )

        content_disposition = (
            f'{disposition}; '
            f'filename="document.pdf"; '
            f"filename*=UTF-8''{encoded_filename}"
        )

        response[
            "Content-Disposition"
        ] = content_disposition

        # ====================================================
        # حجم الملف
        # ====================================================

        response[
            "Content-Length"
        ] = str(
            len(pdf_data)
        )

        logger.info(
            "CONTENT-DISPOSITION: %s",
            content_disposition
        )

        logger.info(
            "CONTENT-LENGTH: %s",
            len(pdf_data)
        )

        logger.info(
            "PDF RESPONSE READY"
        )

        logger.info(
            "========== GENERATE PDF RESPONSE SUCCESS =========="
        )

        return response

    except Exception as e:

        logger.exception(
            "========== GENERATE PDF RESPONSE ERROR =========="
        )

        logger.error(
            "EXCEPTION TYPE: %s",
            type(e).__name__
        )

        logger.error(
            "EXCEPTION MESSAGE: %s",
            str(e)
        )

        return HttpResponse(
            (
                "<!DOCTYPE html>"
                "<html lang='ar' dir='rtl'>"
                "<head>"
                "<meta charset='UTF-8'>"
                "<title>خطأ</title>"
                "</head>"
                "<body>"
                "<h1>حدث خطأ أثناء إنشاء التقرير</h1>"
                "<p>تعذر إنشاء ملف PDF.</p>"
                "</body>"
                "</html>"
            ),
            status=500,
            content_type=(
                "text/html; charset=utf-8"
            )
        )


# ============================================================
# REPORT
# ============================================================

def outpu_report_masah_nah_to_moatn(
    request,
    id
):

    try:

        logger.info(
            "REPORT START | id=%s",
            id
        )


        # ====================================================
        # التقرير
        # ====================================================

        masah = get_object_or_404(
            report_masahi,
            id=id
        )


        # ====================================================
        # تسجيل الطباعة
        # ====================================================

        masah.print_nah = True

        masah.save(
            update_fields=[
                "print_nah"
            ]
        )


        # ====================================================
        # FORM
        # ====================================================

        xx = masah.form


        # ====================================================
        # الحدود
        # ====================================================

        f = (
            Shift_form_hadod.objects
            .filter(
                report_masahi=masah
            )
        )


        # ====================================================
        # LOCATION
        # ====================================================

        ss = (
            Location.objects
            .filter(
                form=xx
            )
            .first()
        )


        # ====================================================
        # صورة رأس التقرير
        # ====================================================

        image_path = (
            get_report_image_path()
        )

        image_base64 = (
            image_to_base64(
                image_path
            )
        )


        # ====================================================
        # صورة الموقع
        # ====================================================

        location_image_base64 = (
            image_field_to_base64(
                masah.location
            )
        )


        logger.info(
            "LOCATION IMAGE | name=%s | base64=%s",
            getattr(
                masah.location,
                "name",
                None
            ),
            bool(
                location_image_base64
            )
        )


        # ====================================================
        # TEMPLATE
        # ====================================================

        template = get_template(
            "masha/"
            "outpu_report_masah_nah_to_moatn.html"
        )


        # ====================================================
        # HTML
        # ====================================================

        html = template.render({

            "f":
                f,

            "masah":
                masah,

            "ss":
                ss,

            "xx":
                xx,

            "image_base64":
                image_base64,

            "location_image_base64":
                location_image_base64,

        })


        # ====================================================
        # PDF NAME
        # ====================================================

        person_name = (
            getattr(
                xx,
                "name",
                ""
            )
            or
            f"id_{masah.id}"
        )


        person_name = (
            clean_pdf_filename(
                person_name
            )
        )


        pdf_filename = (
            f"تقرير مساحي_"
            f"{person_name}_"
            f"{masah.id}.pdf"
        )


        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=False

        )


    except Exception as e:

        logger.exception(
            "ERROR REPORT | id=%s",
            id
        )

        return HttpResponse(

            f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">

            <head>
                <meta charset="UTF-8">
                <title>خطأ</title>
            </head>

            <body>

                <h2>
                    حدث خطأ أثناء إنشاء التقرير
                </h2>

                <p>
                    {str(e)}
                </p>

            </body>

            </html>
            """,

            status=500,

            content_type=
                "text/html; charset=utf-8"

        )
# ============================================================
# تقرير إصدار الاستمارة
# ============================================================
# ============================================================
# إصدار الاستمارة - تقرير
# ============================================================

def asder_astmart_location_report(
    request,
    id
):

    try:

        # ====================================================
        # جلب الطلب
        # ====================================================

        form = get_object_or_404(
            Form,
            id=id
        )

        # ====================================================
        # تسجيل الإصدار
        # ====================================================

        form.exit_eng = True

        form.save(
            update_fields=[
                "exit_eng"
            ]
        )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/asder_astmart_location.html"
        )

        html = template.render({

            "form": form,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                form,
                "name",
                f"id_{form.id}"
            )
        )

        if not person_name:

            person_name = f"id_{form.id}"

        pdf_filename = (

            f"{person_name}"
            f"_تقرير_إصدار_استمارة_"
            f"{form.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in asder_astmart_location_report | id=%s",
            id
        )

        return HttpResponse(
            "حدث خطأ أثناء إنشاء تقرير إصدار الاستمارة.",
            status=500,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# إصدار الاستمارة
# ============================================================

def asder_astmart_location(
    request,
    id
):

    try:

        # ====================================================
        # جلب الطلب
        # ====================================================

        form = get_object_or_404(
            Form,
            id=id
        )

        # ====================================================
        # تسجيل الإصدار
        # ====================================================

        form.exit_eng = True

        form.save(
            update_fields=[
                "exit_eng"
            ]
        )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/asder_astmart_location.html"
        )

        html = template.render({

            "form": form,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                form,
                "name",
                f"id_{form.id}"
            )
        )

        if not person_name:

            person_name = f"id_{form.id}"

        pdf_filename = (

            f"{person_name}_"
            f"{form.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in asder_astmart_location | id=%s",
            id
        )

        return HttpResponse(
            "حدث خطأ أثناء إصدار الاستمارة.",
            status=500,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# طلب استكمال الوثيقة الناقصة
# ============================================================

def talb_astkmal_by_manger(
    request,
    id
):

    try:

        # ====================================================
        # جلب الطلب
        # ====================================================

        aa = get_object_or_404(
            Form,
            id=id,
            talb_astkml=True
        )

        # ====================================================
        # تسجيل التسليم
        # ====================================================

        aa.tslem_astkmal = True

        aa.save(
            update_fields=[
                "tslem_astkmal"
            ]
        )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/talb_astkmal_by_manger.html"
        )

        html = template.render({

            "aa": aa,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                aa,
                "name",
                f"id_{aa.id}"
            )
        )

        if not person_name:

            person_name = f"id_{aa.id}"

        pdf_filename = (

            f"{person_name}"
            f"_طلب_استكمال_الوثيقة_الناقصة_"
            f"{aa.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in talb_astkmal_by_manger | id=%s",
            id
        )

        return HttpResponse(
            "حدث خطأ أثناء إنشاء طلب استكمال الوثيقة.",
            status=500,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# طلب رفع مساحي لغرض البناء
# ============================================================

def tslam(
    request
):

    try:

        # ====================================================
        # جلب أول طلب
        # ====================================================

        aa = Form.objects.first()

        if not aa:

            return HttpResponse(
                "لا يوجد بيانات للطباعة",
                status=404,
                content_type="text/html; charset=utf-8"
            )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/tslam.html"
        )

        html = template.render({

            "aa": aa,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                aa,
                "name",
                f"id_{aa.id}"
            )
        )

        if not person_name:

            person_name = f"id_{aa.id}"

        pdf_filename = (

            f"{person_name}"
            f"_طلب_رفع_مساحي_للغرض_البناء_"
            f"{aa.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in tslam"
        )

        return HttpResponse(
            "حدث خطأ أثناء إنشاء الطلب.",
            status=500,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# طلب رفض رفع مساحي
# ============================================================

def rafth_astmarh_nah(
    request,
    id
):

    try:

        # ====================================================
        # جلب الطلب
        # ====================================================

        aa = get_object_or_404(
            Form,
            id=id,
            rafth_maml=True
        )

        # ====================================================
        # تسجيل تسليم الرفض
        # ====================================================

        aa.tslem_rafth = True

        aa.save(
            update_fields=[
                "tslem_rafth"
            ]
        )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/rafth_masha_by_manger.html"
        )

        html = template.render({

            "aa": aa,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                aa,
                "name",
                f"id_{aa.id}"
            )
        )

        if not person_name:

            person_name = f"id_{aa.id}"

        pdf_filename = (

            f"{person_name}"
            f"_طلب_رفض_رفع_مساحي_"
            f"{aa.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in rafth_astmarh_nah | id=%s",
            id
        )

        return HttpResponse(
            "حدث خطأ أثناء إنشاء طلب الرفض.",
            status=500,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# طلب تسليم
# ============================================================

def tslam_id(
    request,
    id
):

    try:

        # ====================================================
        # جلب الطلب
        # ====================================================

        aa = get_object_or_404(
            Form,
            id=id
        )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/tslam.html"
        )

        html = template.render({

            "aa": aa,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                aa,
                "name",
                f"id_{aa.id}"
            )
        )

        if not person_name:

            person_name = f"id_{aa.id}"

        pdf_filename = (

            f"{person_name}"
            f"_طلب_تسليم_"
            f"{aa.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in tslam_id | id=%s",
            id
        )

        return HttpResponse(
            "حدث خطأ أثناء إنشاء طلب التسليم.",
            status=500,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# طلب رفع مساحي استشارة
# ============================================================

def tslam_astsh(
    request
):

    try:

        # ====================================================
        # جلب أول سجل
        # ====================================================

        aa = Form.objects.first()

        if not aa:

            return HttpResponse(
                "لا يوجد بيانات للطباعة",
                status=404,
                content_type="text/html; charset=utf-8"
            )

        # ====================================================
        # الصورة
        # ====================================================

        image_path = get_report_image_path()

        image_base64 = image_to_base64(
            image_path
        )

        # ====================================================
        # القالب
        # ====================================================

        template = get_template(
            "masha/tslem_astsh.html"
        )

        html = template.render({

            "aa": aa,

            "image_base64": image_base64,

        })

        # ====================================================
        # اسم الملف
        # ====================================================

        person_name = clean_pdf_filename(
            getattr(
                aa,
                "name",
                f"id_{aa.id}"
            )
        )

        if not person_name:

            person_name = f"id_{aa.id}"

        pdf_filename = (

            f"{person_name}"
            f"_طلب_رفع_مساحي_استشارة_"
            f"{aa.id}.pdf"

        )

        # ====================================================
        # PDF
        # ====================================================

        return generate_pdf_response(

            html,

            pdf_filename,

            inline=True

        )

    except Exception:

        logger.exception(
            "ERROR in tslam_astsh"
        )

        return HttpResponse(
            "حدث خطأ أثناء إنشاء طلب الاستشارة.",
            status=500,
            content_type="text/html; charset=utf-8"
        )
def show_intreface(request):
    return render(request,'masha/show_intreface.html')


def is_admin_or_has_permission(user):
    return user.is_superuser or user.has_perm("masha.add_form")

@coordinator_or_manager_required
@mahfth_screen_required
def enter_data_report_masahi(request):
    
    ty=typ.objects.all()
    saf=Safah.objects.all()
    mah=visible_mahfth_list(request.user)
    ass=AStmrah.objects.get(id="1")
    val=Vald_doc.objects.all()
    val_m =Vald_tharb.objects.all()
    zz=User.objects.get(username=request.user)
    

    


    context={'mah':mah,'ty':ty,'zz':zz,'saf':saf,'ass':ass,'val':val,'val_m':val_m}

    
    

    return render(request,'masha/enter_data_report_masahi.html',context)
@csrf_exempt


@coordinator_or_manager_required
def form_add_masah(request):
    if request.method == "POST":

        date_str = request.POST.get('date_str')
        name = request.POST.get('name_aml')
        asher = request.POST.get('asher')
        service_list_form_x = request.POST.get('service_list_form_x')
        streat_name_gr = request.POST.get('streat_name_gr')
        hid_mah = request.POST.get('hid_mah')
        checkbox_data = request.POST.getlist('basert')

        img_parsone = request.FILES.get('img_parsone', "")
        img_document = request.FILES.get('img_document', "")

        hid_gata = request.POST.get('hid_gata')
        streat_name = request.POST.get('streat_name')
        text_36 = request.POST.get('text_36')
        phone = request.POST.get('phone')

        card_id = request.POST.get('card_id')
        month = request.POST.get('month')
        year = request.POST.get('year')
        typp = request.POST.get('hid_type_document')

        erea_baser = request.POST.get('erea_11')
        document_number = request.POST.get('number_dcoum_in_t')
        hidden_type_aqure = request.POST.get('hid_type_aqure')

        name_wk = request.POST.get('f2')
        phone_wk = request.POST.get('f4')
        card_id_wk = request.POST.get('f6')

        hid_type_form_rakash = request.POST.get('hid_type_form_rakash', '').strip()
        hid_ansh_hdm = request.POST.get('hid_ansh_hdm', '').strip()

        # المستخدم العادي لا يستطيع اختيار مديرية غير مديريته
        mahfth, mahfth_error = resolve_mahfth_for_user(request.user, hid_mah)
        if mahfth is None:
            return HttpResponse(mahfth_error or "مديرية غير صحيحة", status=403)
        typ_a = typ.objects.get(name=typp)

        if hid_type_form_rakash == "صاحب الطلب" and hid_ansh_hdm != "استشارة":

            f = Form.objects.create(
                name=name,
                asher=asher,
                phone=phone,
                card_id=card_id,
                img_parsone=img_parsone,
                img_document=img_document,
                typ=typ_a,
                erea_baser=erea_baser,
                document_number=document_number,
                typ_aqur=hidden_type_aqure,
                saft_sahb_talab=hid_type_form_rakash,
                ajaml=text_36,
                month=month,
                year=year,
                sent_att=date_str,
                streat_name=streat_name,
                name_wk=name,
                card_id_wk=card_id,
                hidden_ansh_hdm=hid_ansh_hdm,
                mahfth=mahfth
            )
            return HttpResponse(status=200)

        elif hid_type_form_rakash == "صاحب الطلب" and hid_ansh_hdm == "استشارة":

            rr = Type_talb_astshr.objects.filter(id=service_list_form_x).first() if str(service_list_form_x or '').isdigit() else None
            f = Form.objects.create(
                name=name,
                phone=phone,
                streat_name_gr=streat_name_gr,
                asher=asher,
                card_id=card_id,
                erea_baser=erea_baser,
                document_number=document_number,
                typ_aqur=hidden_type_aqure,
                typ=typ_a,
                saft_sahb_talab=hid_type_form_rakash,
                ajaml=text_36,
                month=month,
                year=year,
                sent_att=date_str,
                streat_name=streat_name,
                type_talb_astshr=rr,
                name_wk=name,
                card_id_wk=card_id,
                hidden_ansh_hdm=hid_ansh_hdm,
                mahfth=mahfth
            )
            return HttpResponse(status=200)

        elif hid_type_form_rakash != "صاحب الطلب" and hid_ansh_hdm != "استشارة":

            f = Form.objects.create(
                name=name,
                mahfth=mahfth,
                sent_att=date_str,
                asher=asher,
                phone=phone,
                card_id=card_id,
                typ=typ_a,
                erea_baser=erea_baser,
                document_number=document_number,
                typ_aqur=hidden_type_aqure,
                saft_sahb_talab=hid_type_form_rakash,
                name_wk=name_wk,
                phone_wk=phone_wk,
                card_id_wk=card_id_wk,
                month=month,
                year=year,
                streat_name=streat_name,
                ajaml=text_36,
                hidden_ansh_hdm=hid_ansh_hdm
            )
            return HttpResponse(status=200)

        else:
            rr = Type_talb_astshr.objects.filter(id=service_list_form_x).first() if str(service_list_form_x or '').isdigit() else None
            f = Form.objects.create(
                name=name,
                streat_name_gr=streat_name_gr,
                type_talb_astshr=rr,
                mahfth=mahfth,
                sent_att=date_str,
                asher=asher,
                phone=phone,
                card_id=card_id,
                erea_baser=erea_baser,
                document_number=document_number,
                img_parsone=img_parsone,
                img_document=img_document,
                typ_aqur=hidden_type_aqure,
                saft_sahb_talab=hid_type_form_rakash,
                name_wk=name_wk,
                phone_wk=phone_wk,
                card_id_wk=card_id_wk,
                month=month,
                year=year,
                typ=typ_a,
                streat_name=streat_name,
                ajaml=text_36,
                hidden_ansh_hdm=hid_ansh_hdm
            )
            return HttpResponse(status=200)

        

    
def insert_to_image_talb(request):
     pass

@csrf_exempt

def talb_add_to_base_trhle(request) :
    if request.method=="POST":
    
     talbt=request.FILES.get('talbt', "")
     number=request.POST['number']
     tal,created=Talb.objects.get_or_create(id=number)
     #vald_a=Vald.objects.get(name=tal.vald)
     typ_a=typ.objects.get(name=tal.typ)
     unit = Unit.objects.get(name=tal.unit)
     
     
    
     

    
     f=Form.objects.create(name=tal.name,phone=tal.phone,card_id=tal.card_id,img_parsone=tal.img_parsone,img_document=tal.img_document,erea_baser=tal.erea_baser,document_number=tal.document_number,streat_name=tal.streat_name, typ_aqur=tal.typ_aqur,saft_sahb_talab=tal.saft_sahb_talab ,name_wk=tal.name_wk,phone_wk=tal.phone_wk,card_id_wk=tal.card_id_wk,ajaml=tal.ajaml,unit=unit) 
     tal.delete()
     return HttpResponse(status=200)
import os
import base64
import mimetypes


def image_to_base64(image_path):

    if not image_path:
        return ""

    if not os.path.isfile(image_path):
        return ""

    try:

        with open(image_path, "rb") as image_file:

            encoded = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        mime_type, _ = mimetypes.guess_type(
            image_path
        )

        if not mime_type:
            mime_type = "image/jpeg"

        return (
            f"data:{mime_type};base64,{encoded}"
        )

    except Exception as e:

        print(
            f"خطأ في قراءة الصورة: {e}"
        )

        return ""
@login_required
def agree_tsrah_xx(request):
    role = get_space_role(request.user)
    if not (is_manager(request.user) or role == SPACE_ROLE_HEAD):
        return render(request, 'masha/no_permission.html', status=403)

    forms = Form.objects.filter(
        show_tasrah_karoj=False,
        rafth_maml=False,
        talb_astkml=False,
        return_form=False,
        digital=False,
    )
    form = filter_forms(forms, request.user).order_by('-id')
    context = {'form': form, 'zz': request.user}
    return render(request, 'masha/agree_to_tsrah_kroj.html', context)
@mahfth_screen_required
def add_motan_service_jamhore_to_fane(request,id):
    eng_nazol=Eng_nazol.objects.all()

    
    
    f=Form.objects.get(id=id)
    zz=User.objects.get(username=request.user)
    


    context={'eng_nazol':eng_nazol,'zz':zz,'f':f}
    
    return render(request,'masha/add_unit_to_masha.html',context)
def is_admin_or_has_permission(user):
    return user.is_superuser or user.has_perm("masha.add_form")
@mahfth_screen_required
def serch_page_talb_bana(request):
    return render(request,'masha/serch_page_talb_bana.html')
def is_admin_or_has_permission(user):
    return user.is_superuser or user.has_perm("masha.add_form")
@mahfth_screen_required
def search_edit_form_talb_bana(request,id):

    ty = typ.objects.all()
    saf = Safah.objects.all()
    mah = visible_mahfth_list(request.user)
    astmrah =AStmrah.objects.all()
    ass = get_object_or_404(Form, id=id)
    val = Vald_doc.objects.all()
    val_m = Vald_tharb.objects.all()
    zz = request.user

    context = {
        'mah': mah,
        'ty': ty,
        'zz': zz,
        'saf': saf,
        'ass': ass,
        'val': val,
        'val_m': val_m,
        'astmrah':astmrah,
    }

    return render(request, 'masha/masahi_form.html', context)




def update_request(request, id):
    ass = get_object_or_404(Form, id=id)

    if request.method == "POST":
        # العلاقات
        ass.saft_sahb_talab = request.POST.get("list_form")
        ass.astmarah = AStmrah.objects.get(name=request.POST.get("ansh_hdm"))
        ass.typ = typ.objects.get(name=request.POST.get("type_document"))
        new_mahfth, mahfth_error = resolve_mahfth_for_user(request.user, request.POST.get("mderah"))
        if new_mahfth is None:
            return HttpResponse(mahfth_error or "مديرية غير صحيحة", status=403)
        ass.mahfth = new_mahfth
       

        # الحقول العادية
        ass.card_id = request.POST.get("card_id")
        ass.phone = request.POST.get("phone")
        ass.name = request.POST.get("name")
        ass.name_wk = request.POST.get('name')
        ass.streat_name = request.POST.get("streat_name")
        ass.streat_name_gr = request.POST.get("streat_name_gr")
        
        ass.vald_document = request.POST.get("vald_document")
        ass.erea_baser = request.POST.get("erea_baser")

        ass.save()

        messages.success(request, "✅ تم تعديل الطلب بنجاح")
        return redirect("masha:enter_data_report_masahi_screen")




def show_astmrah(request,id):
    aa=Form.objects.get(id=id)
    context={'aa':aa}
    return render(request,'masha/show_astmrah.html',context)
@csrf_exempt
def add_unit_nah_eng_masha(request):
    if request.method=="POST":
        
        rasone_rafth_maml=request.POST['rasone_rafth_maml']
        show_astkmal_id=request.POST['show_astkmal_id']
        eng_name=request.POST['eng_name']
        rasone_rafth_maml=request.POST['rasone_rafth_maml']
        ex = request.POST.get('ex')
        number=request.POST['number']
        if ex =='منجزة':
            form,created=Form.objects.get_or_create(id=number)
            form.sender=request.user
            form.is_readt=True
            form.show_tasrah_karoj=True
            form.angaz_1=ex
            form.eng_nazol=eng_name
            form.save()
            return HttpResponse(status=200)
        elif ex=='رفض':
            form,created=Form.objects.get_or_create(id=number)
            form.sender=request.user
            form.rasone_rafth_maml=rasone_rafth_maml
            form.is_readt=True
            form.rafth_maml=True
            form.angaz_1=ex
            form.eng_nazol=eng_name
            form.save()
            return HttpResponse(status=200)
        elif ex== 'استكمال  '  :
            form,created=Form.objects.get_or_create(id=number)
            form.sender=request.user
            form.is_readt=True
            form.talb_astkml=True
            
            form.angaz_1=ex
            form.name_documnt=show_astkmal_id
            form.eng_nazol=eng_name
            form.save()
            return HttpResponse(status=200)

def screen_show_report(request):
         return render(request,'masha/screen_show_report.html')
@space_roles_only(allowed_roles={SPACE_ROLE_ENGINEER})
@mahfth_screen_required
def show_astmrat(request):
    form=filter_forms(Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=True), request.user).count()
    rafth_ald= filter_reports(report_masahi.objects.filter( rafth_adarah_generl=True), request.user).count()
    context={'form':form,'rafth_ald':rafth_ald}
    return render(request,'masha/show_astmrat.html',context)
@user_passes_test(lambda u: u.is_superuser or u.has_perm('masha.add_shift_form_hadod'))
def show_astmrat_json(request):
    form_count = filter_forms(Form.objects.filter(
        show_tasrah_karoj=True,
        return_form=False,
        digital=False,
        tr_masah=False,
        exit_eng=True
    ), request.user).count()
    return JsonResponse({'form': form_count})
    
@mahfth_screen_required
def show_tlabt_nah_rakis(request):
    

       form=filter_forms(Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=True), request.user).order_by('-id')
       context={'form':form}
       return render(request,'masha/show_data_report.html',context)






   
   


@mahfth_screen_required
def search_page(request):
    return render(request, 'masha/search_page.html')
# صفحة البحث
def is_admin_or_has_permission(user):
    return user.is_superuser or user.has_perm("masha.add_form")

@mahfth_screen_required
def search_page_talb(request):
    return render(request, 'masha/search_page_talb.html')
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Form, Unit, Type_map, Type_kah, Type_seol, Type_natural, Type_block, report_masahi, Location

@csrf_exempt
def edit_report_ajax(request,id):
   
    if request.method == "POST":

       
        mnsobe = request.POST.get('mnsobe', '')
        hid_gata = request.POST.get('hid_gata', '')
        opin_en = request.POST.get('opnin_eng', '')
        hid_map_location = request.POST.get('hid_map_location', '')
        hid_block = request.POST.get('hid_block', '')
        hid_seol = request.POST.get('hid_seol', '')
        hid_kah = request.POST.get('hid_kah', '')
        hid_mah = request.POST.get('hid_mah', '')
        hid_nat = request.POST.get('hid_nat', '')
        name = request.POST.get('name', '')

        # ───── استلام الملفات ─────
        mahther_line = request.FILES.get('mahther_line', None)
        location_file = request.FILES.get('location_a', None)

        # ───── استلام checkbox ─────
        

        # ───── استلام الإحداثيات إذا كانت موجودة ─────
        latitude = request.POST.get('point_1', None)
        longitude = request.POST.get('point_2', None)

        # ───── جلب الكائنات المرتبطة بأمان ─────
        try:
            form_obj = Form.objects.get(id=id)
            report=report_masahi.objects.filter(form=form_obj,tr_masah=True,rafth_adarah_generl=False)

        except Form.DoesNotExist:
            return JsonResponse({"error": "Form not found"}, status=404)

        # ─── تحقق من أن القيمة موجودة قبل جلب الـ FK ───
        try:
            unit = Unit.objects.get(id=hid_gata) if hid_gata else None
            type_map_xx = Type_map.objects.get(name=hid_map_location) if hid_map_location else None
            kah = Type_kah.objects.get(name=hid_kah) if hid_kah else None
            seol = Type_seol.objects.get(name=hid_seol) if hid_seol else None
            natural = Type_natural.objects.get(id=hid_nat) if hid_nat else None
            block = Type_block.objects.get(id=hid_block) if hid_block else None

            mah=Mahfth.objects.get(id=hid_mah)if hid_mah else None
        except Exception as e:
            return JsonResponse({"error": f"Related object error: {str(e)}"}, status=400)

        # ───── تحديث نموذج Form ─────
        form_obj.tr_masah = True

        if unit:
            form_obj.unit = unit
        if kah:
            form_obj.type_kah = kah
        if seol:
            form_obj.type_seol = seol
        if natural:
            form_obj.type_natural = natural
        if block:
            form_obj.type_block = block
        if  mah:
             form_obj.mahfth = mah


        form_obj.name = name
        form_obj.save()
        mass, created = report_masahi.objects.get_or_create(form=form_obj)
        mass.tr_masah = True
        mass.rafth_adarah_generl=False
       
        mass.opnine_eng = opin_en
        mass.save()

       
       

        # ───── إنشاء موقع إذا كانت الإحداثيات موجودة ─────
        if hid_map_location == "احدثيات" and latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                Location.objects.create(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    form=form_obj
                )
            except ValueError:
                return JsonResponse({"error": "Invalid coordinates"}, status=400)

        return JsonResponse({"status": "success"}, status=200)

    # إذا لم يكن POST
    return JsonResponse({"error": "Invalid request method"}, status=405)


def live_search_ajax_table(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        # حاول تحويل النص إلى رقم لـ id
        try:
            search_id = int(query)
        except ValueError:
            search_id = None

        matches = Form.objects.filter(
         
           
            Q(name__icontains=query) |
             Q(unit__name__icontains=query) 

        
        )[:100]
        matches = filter_forms(matches, request.user)

        for i in matches:
            rep = getattr(i, "report_masahi", None)
            results.append({
                "typ_name": i.typ.name if i.typ else "",
                "unit_name": i.unit.name if i.unit else "",
                "location_url": rep.location.url if rep and rep.location else "",
                "mahfth_name": i.mahfth.name if i.mahfth else "",
                "img_document_url": i.img_document.url if i.img_document else "",
                "img_parsone_url": i.img_parsone.url if i.img_parsone else "",
                "request_image_url": reverse('masha:tslam_id', args=[i.id]),
                "ajaml": i.ajaml,
                "hidden_ansh_hdm": i.hidden_ansh_hdm,
                "name": i.name,
                "id": i.id
            })

    return JsonResponse({"results": results})


from django.http import JsonResponse
from .models import Unit

def get_units_by_mderah(request):
    if request.method == "POST":
        mderah_id = request.POST.get('mderah_id')
        units = Unit.objects.filter(mahfth_id=mderah_id).values('id', 'name')
        return JsonResponse({'units': list(units)})
    return JsonResponse({'units': []}, status=400)
@user_passes_test(lambda u: u.is_superuser or u.has_perm('masha.add_shift_form_hadod'))
def search_edit_form(request, id):
    form_obj = get_object_or_404(Form, id=id)
    res=Resone.objects.get(id=2)
    mas = report_masahi.objects.filter(name="مساحي",form=form_obj,tr_masah=True,rafth_adarah_generl=True,resone=res).first()
    if not mas:
            messages.error(request, "لايمكنك تعديل بيانات  التقرير")
            return redirect('masha:search_page')
    form_a = get_object_or_404(Form, id=id)
    mderah=visible_mahfth_list(request.user)
    ss=Form.objects.get(id=id)
    xx=Type_map.objects.all()
    kah=Type_kah.objects.all()
    seo=Type_seol.objects.all()
    natural=Type_natural.objects.all()
    block=Type_block.objects.all()

    context={'form_a':form_a,'xx':xx,'kah':kah,'seo':seo,'natural':natural,'block':block,'mderah':mderah}
    return render(request, 'masha/search_edit.html',context)
def is_admin_or_has_permission(user):
    return user.is_superuser or user.has_perm("masha.add_form")
@mahfth_screen_required
def search_edit_form_talb(request, id):
    # جلب العنصر أو إظهار 404 إذا لم يوجد
    # (الوصول مسموح للمدير أو لمستخدم مرتبط بمدينة/مديرية، والبيانات مقيّدة)

    ty = typ.objects.all()
    type_s = Type_talb_astshr.objects.all()
    typ_t = Type_talb.objects.all()
    saf = Safah.objects.all()
    val = Vald_doc.objects.all()
    val_m = Vald_tharb.objects.all()
    ass = get_object_or_404(Form,id=id)
    form_a=Form.objects.get(id=id)
    zz = request.user

    mah = visible_mahfth_list(request.user)

    context = {
        'mah': mah,
        'ty': ty,
        'zz': zz,
        'type_s': type_s,
        'typ_t': typ_t,
        'saf': saf,
        'ass': ass,
        'val': val,
        'val_m': val_m,
        'form_a':form_a
    }

    return render(request, 'masha/update_talbt_form_by_manger.html',context)

@mahfth_screen_required
def edit_form_talb(request, id):
    if request.method == "POST":
        ass = get_object_or_404(Form, id=id)
        errors = {}

        # التحقق من الحقول المطلوبة
        if not request.POST.get('card_id'):
            errors['card_id'] = 'هذا الحقل مطلوب'
        if not request.POST.get('name'):
            errors['name'] = 'هذا الحقل مطلوب'
        if not request.POST.get('phone'):
            errors['phone'] = 'هذا الحقل مطلوب'
        if not request.POST.get('typ'):
            errors['typ'] = 'اختر نوع الوثيقة'

        if errors:
            return JsonResponse({'status': 'fail', 'errors': errors}, status=400)

        # حفظ البيانات
        ass.card_id = request.POST.get('card_id')
        ass.phone = request.POST.get('phone')
        list_form_x= request.POST.get('list_form_x')
        ass.name = request.POST.get('name')
        ass.name_wk = request.POST.get('name')
        ass.streat_name = request.POST.get('streat_name')
        ass.streat_name_gr = request.POST.get('streat_name_gr')
        xx = request.POST.get('typ')
        ass.ansh_hdm = request.POST.get('ansh_hdm')
        ass.card_id_wk = request.POST.get('card_id_wk')
        ass.phone_wk = request.POST.get('phone_wk')
        ass.name_wk = request.POST.get('name_wk')
        mderah_id = request.POST.get('mderah')
        list_form = request.POST.get('list_form')
        
        if mderah_id:
            new_mahfth, mahfth_error = resolve_mahfth_for_user(request.user, mderah_id)
            if new_mahfth is None:
                return JsonResponse({'status': 'fail', 'errors': {'mderah': mahfth_error}}, status=403)
            ass.mahfth = new_mahfth
        if xx :
            ass.typ=typ.objects.get(name=xx)
        if list_form_x:
             ass.type_talb_astshr=Type_talb_astshr.objects.get(id=list_form_x)
        if list_form:
            ass.safah=Safah.objects.get(name=list_form)
        ass.vald_document = request.POST.get('vald_document')
        ass.year = request.POST.get('year')
        ass.month_a = request.POST.get('month_a')
        ass.save()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail', 'msg': 'غير مسموح'}, status=400)


# غيّر هذا إلى اسم الموديل الخاص بك
from django.db.models import Q

def live_search_ajax_hadod_a(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        matches = Form.objects.filter(
            Q(name__icontains=query) | Q(id__icontains=query)
        )[:50]  # الحد الأعلى للنتائج

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "typ_name": obj.typ.name if obj.typ else '',
                "unit_name": obj.unit.name if obj.unit else '',
                "hidden_ansh_hdm":obj.hidden_ansh_hdm ,
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "img_document": obj.img_document.url if obj.img_document else '',
            })

    return JsonResponse({"results": results})

def live_search_ajax(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        matches = Form.objects.filter(
            Q(name__icontains=query,hidden_ansh_hdm="استشارة") | Q(id__icontains=query)
        )[:50]  # الحد الأعلى للنتائج
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "typ_name": obj.typ.name if obj.typ else '',
                "unit_name": obj.unit.name if obj.unit else '',
                "hidden_ansh_hdm":obj.hidden_ansh_hdm ,
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "img_document": obj.img_document.url if obj.img_document else '',
            })

    return JsonResponse({"results": results})
def live_search_ajax_report(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        matches = Form.objects.filter(
            Q(name__icontains=query) | Q(id__icontains=query)
        )[:50]  # الحد الأعلى للنتائج
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "typ_name": obj.typ.name if obj.typ else '',
                "unit_name": obj.unit.name if obj.unit else '',
                "hidden_ansh_hdm":obj.hidden_ansh_hdm ,
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "img_document": obj.img_document.url if obj.img_document else '',
            })

    return JsonResponse({"results": results})
def live_search_ajax_bana(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        matches = Form.objects.filter(
            Q(name__icontains=query,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص") | Q(id__icontains=query)
        )[:50]  # الحد الأعلى للنتائج
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "typ_name": obj.typ.name if obj.typ else '',
                "unit_name": obj.unit.name if obj.unit else '',
                "hidden_ansh_hdm":obj.hidden_ansh_hdm ,
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "img_document": obj.img_document.url if obj.img_document else '',
            })

    return JsonResponse({"results": results})

# صفحة تعديل البيانات
def edit_form(request, id):
    form_obj = get_object_or_404(Form, id=id)

    if request.method == 'POST':
        # تحديث البيانات مباشرة من request.POST
        form_obj.erea_asqt = request.POST.get('erea_asqt', '')
        form_obj.name = request.POST.get('name', '')
        form_obj.type_block = request.POST.get('type_block', '')
        form_obj.type_seol = request.POST.get('type_seol', '')
        form_obj.type_kah = request.POST.get('type_kah', '')
        form_obj.type_natural = request.POST.get('type_natural', '')
        form_obj.mderah_id = request.POST.get('mderah', None)
        form_obj.unit_id = request.POST.get('unit', None)
        form_obj.opnine_eng = request.POST.get('opin_en', '')
        # يمكن إضافة باقي الحقول بنفس الطريقة

        form_obj.save()
        return redirect('masha:search_edit_form')  # بعد التعديل ارجع للبحث

    return render(request, 'masha/search_edit.html', {'form': form_obj})


@mahfth_screen_required
def astkmal_report_masah_nah(request,id):
   
      form=Form.objects.get(id=id)
      form_a=Form.objects.get(id=id)
     
      unt = Unit.objects.filter(mahfth=form.mahfth)

   

      xx=Type_map.objects.all()
      kah=Type_kah.objects.all()
      seo=Type_seol.objects.all()
      natural=Type_natural.objects.all()
      block=Type_block.objects.all()
      context={'form':form,'form_a':form_a,'xx':xx,'kah':kah,'seo':seo,'natural':natural,'block':block,'unt':unt}
      return render(request,'masha/show_report_masahi_nah.html',context)

@csrf_exempt
def add_abade_report_masahi(request, id):
    if request.method == "POST":
        # ───── استلام القيم النصية ─────
        mnsobe = request.POST.get('mnsobe', '')
        hid_gata = request.POST.get('hid_gata', '')
        opin_en = request.POST.get('opin_en', '')
        hid_map_location = request.POST.get('hid_map_location', '')
        hid_block = request.POST.get('hid_block', '')
        hid_seol = request.POST.get('hid_seol', '')
        hid_kah = request.POST.get('hid_kah', '')
        hid_nat = request.POST.get('hid_nat', '')
        #erea_asqt = request.POST.get('e_11', '')
        name = request.POST.get('name', '')

        # ───── استلام الملفات ─────
        mahther_line = request.FILES.get('mahther_line', None)
        location_file = request.FILES.get('location_a', None)

        # ───── استلام checkbox ─────
        tr_masah = request.POST.get('tr_masah', '')
        ss = True if tr_masah == "منجزة" else False

        # ───── استلام الإحداثيات إذا كانت موجودة ─────
        latitude = request.POST.get('point_1', None)
        longitude = request.POST.get('point_2', None)

        # ───── جلب الكائنات المرتبطة ─────
        try:
            unit = Unit.objects.get(id=hid_gata)
            type_map_xx = Type_map.objects.get(name=hid_map_location)
            kah = Type_kah.objects.get(name=hid_kah)
            seol = Type_seol.objects.get(name=hid_seol)
            natural = Type_natural.objects.get(id=hid_nat)
            block = Type_block.objects.get(id=hid_block)
            form_obj = Form.objects.get(id=id)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=400)

        # ───── تحديث نموذج Form ─────
        form_obj.tr_masah = ss
        #form_obj.erea_asqt = erea_asqt
        form_obj.unit = unit
        form_obj.type_kah = kah
        form_obj.type_seol = seol
        form_obj.type_natural = natural
        form_obj.type_block = block
        form_obj.save()

        # ───── تحديث تقرير report_masahi ─────
        mass, created = report_masahi.objects.get_or_create(form=form_obj)
        mass.tr_masah = ss
        mass.return_masah_jm = False
        mass.opnine_eng = opin_en
        #mass.erea_asqt = erea_asqt
        mass.kml_file = mahther_line
        mass.location = location_file
        mass.type_map = type_map_xx
        mass.mnsobe=mnsobe
        mass.save()
        aa=mass.form.id
        form,created=Form.objects.get_or_create(id=aa)
        xx=form.width_street_big_not
        asd=10.0
        if xx<asd:
            form.broze=0
        elif xx>asd and xx<=12.0:
            form.broze=0.75
        else:
            form.broze=1
        form.save()

        # ───── إنشاء موقع إذا كانت الإحداثيات موجودة ─────
        if hid_map_location == "إحداثيات" and latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                Location.objects.create(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    form=form_obj
                )
            except ValueError:
                return HttpResponse("Invalid coordinates", status=400)

        return HttpResponse(status=200)

    return HttpResponse(status=405)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import report_masahi

@login_required
def agree_rafth_report_masah_nah_tamp(request):
    zz = request.user

    if request.user.is_superuser:
        # المشرف يرى كل النماذج التي تحتاج موافقة
        show_manger_form = report_masahi.objects.filter(
            tr_masah=True,
            return_masah_jm=False,
            rafth_adarah_generl=False,
            masahi_convert=False
        )
    else:
        # المستخدم العادي يرى فقط النماذج المتعلقة به
        try:
            phone_number = zz.profile.phone_number
            show_manger_form = report_masahi.objects.filter(
                tr_masah=True,
                return_masah_jm=False,
                rafth_adarah_generl=False,
                masahi_convert=False,
                form__asher=phone_number   # حسب علاقة الـ form
            )
        except AttributeError:
            show_manger_form = report_masahi.objects.none()  # لا توجد بيانات

    context = {
        'show_manger_form': show_manger_form,
        'zz': zz
    }

    return render(request, 'masha/agree_rafth_report_masah_nah_tamp.html', context)
def serch_talbt_report_by_mnager_nah(request):
    form=report_masahi.objects.filter( tr_masah=True,
            return_masah_jm=False,
            rafth_adarah_generl=False,
            masahi_convert=False,
            agree_adarah_generl_by_manager_mahfth=False,
            rafth_adarah_generl_by_manager_mahfth=False)
    context={'form':form}
    return render(request, 'masha/serch_talbt_report_by_mnager_nah.html',context)
from django.http import JsonResponse
from django.db.models import Q

from django.http import JsonResponse
from django.db.models import Q

def live_search_ajax_report_masha(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(form__name__icontains=query)

        if query.isdigit():
            filters |= Q(id=query)

        matches = report_masahi.objects.select_related(
            "form",
          
            "type_map"
        ).filter(
            filters,
            tr_masah=True,
            return_masah_jm=False,
            rafth_adarah_generl=False,
            masahi_convert=False,
            agree_adarah_generl_by_manager_mahfth=False,
            rafth_adarah_generl_by_manager_mahfth=False
        )[:50]
        matches = filter_reports(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.form.name if obj.form else '',
                "typ_name": obj.type_map.name if obj.type_map else '',
               "unit_name": obj.form.unit.name if obj.form and hasattr(obj.form, 'unit') else '',
               "gata_name": obj.form.gata.name if obj.form and hasattr(obj.form, 'gata') else '',
                "mahfth_name": obj.form.mahfth.name if obj.resone else '',
                "img_document": '',
                "kml_file": obj.kml_file.url if obj.kml_file else '',  # 
            })

    return JsonResponse({"results": results})
    return JsonResponse(results, safe=False)
def live_search_ajax_report_masha_to_generle_adarah(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(form__name__icontains=query)

        if query.isdigit():
            filters |= Q(id=query)

        matches = report_masahi.objects.select_related(
            "form",
            "resone",
            "type_map"
        ).filter(
            filters,
            tr_masah=True,return_masah_jm=False,rafth_adarah_generl=False,masahi_convert=True,convert_agin=False,convert_agin_agree=False,agree_adarah_generl_by_manager_mahfth=False,rafth_adarah_generl_by_manager_mahfth=False
        )[:50]
        matches = filter_reports(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.form.name if obj.form else '',
                "typ_name": obj.type_map.name if obj.type_map else '',
               "unit_name": obj.form.unit.name if obj.form and hasattr(obj.form, 'unit') else '',
               "gata_name": obj.form.gata.name if obj.form and hasattr(obj.form, 'gata') else '',
                "mahfth_name": obj.resone.name if obj.resone else '',
                "img_document": '',
                "kml_file": obj.kml_file.url if obj.kml_file else '',  # 
            })

    return JsonResponse({"results": results})
    return JsonResponse(results, safe=False)

def live_search_ajax_report_masha_to_agree_manager_generl_mang(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(form__name__icontains=query)

        if query.isdigit():
            filters |= Q(id=query)

        matches = report_masahi.objects.select_related(
            "form",
           
            "type_map"
        ).filter(
            filters,
            agree_adarah_generl_by_manager_mahfth=True
        )[:50]
        matches = filter_reports(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.form.name if obj.form else '',
                "typ_name": obj.type_map.name if obj.type_map else '',
               "unit_name": obj.form.unit.name if obj.form and hasattr(obj.form, 'unit') else '',
               "mahfth_name": obj.form.mahfth.name if obj.form and hasattr(obj.form, 'gata') else '',
              
                "img_document": '',
                "kml_file": obj.kml_file.url if obj.kml_file else '',  # 
            })

    return JsonResponse({"results": results})
    return JsonResponse(results, safe=False)
def serch_agree_tsrah_karoj(request):
    return render(request,'masha/serch_agree_tsrah_karoj.html',context)

@space_roles_only(block_management=True)
def show_convert_to_mashi_from_fero(request):
            show_manger_form=report_masahi.objects.filter(tr_masah=True,return_masah_jm=False,rafth_adarah_generl=False,masahi_convert=True,convert_agin=False,convert_agin_agree=False,agree_adarah_generl_by_manager_mahfth=False,rafth_adarah_generl_by_manager_mahfth=False)
            context={'show_manger_form':show_manger_form}
            return render(request,'masha/show_convert_to_mashi_from_fero.html',context)
def show_convert_to_mashi_from_fero_nah(request):
            show_manger_form=report_masahi.objects.filter(agree_adarah_generl_by_manager_mahfth=True)
            context={'show_manger_form':show_manger_form}
            return render(request,'masha/show_convert_to_mashi_from_fero_nah.html',context)
@space_roles_only(block_management=True)
def show_convert_to_mashi_from_fero_nah_adrah(request):
        show_manger_form=report_masahi.objects.filter(agree_adarah_generl_by_manager_mahfth=True)
        context={'show_manger_form':show_manger_form}
        return render(request,'masha/show_convert_to_mashi_from_fero_nah_aldarha.html',context)


def live_search_ajax_report_masha_to_rafth_aldarah_to_report(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(form__name__icontains=query)

        if query.isdigit():
            filters |= Q(id=query)

        matches = report_masahi.objects.select_related(
            "form",
          
            "type_map"
        ).filter(
            filters,
           rafth_adarah_generl_by_manager_mahfth=True
        )[:50]
        matches = filter_reports(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.form.name if obj.form else '',
                "typ_name": obj.type_map.name if obj.type_map else '',
               "unit_name": obj.form.unit.name if obj.form and hasattr(obj.form, 'unit') else '',
               "mahfth_name": obj.form.mahfth.name if obj.form and hasattr(obj.form, 'mahfth') else '',
               "resone_refth_adrah": obj.resone_refth_adrah  ,
                "img_document": '',
                "kml_file": obj.kml_file.url if obj.kml_file else '',  # 
            })

    return JsonResponse({"results": results})
@space_roles_only(block_management=True)
def rafth_by_manager_aldarah_generl_nah(request):
           show_manger_form=report_masahi.objects.filter(rafth_adarah_generl_by_manager_mahfth=True)
           context={'show_manger_form':show_manger_form}
           return render(request,'masha/reason_rafth_managmnat_generl.html',context)
def reason_rafth_managmnat_generl_to_convert_maderah(request):
           show_manger_form=report_masahi.objects.filter(rafth_adarah_generl_by_manager_mahfth=True)
           context={'show_manger_form':show_manger_form}
           return render(request,'masha/reason_rafth_managmnat_generl_to_convert_maderah.html',context)
@space_roles_only(allowed_roles={SPACE_ROLE_HEAD})
@mahfth_screen_required
def show_manager_masah_nah(request):
    # جلب المستخدم الحالي ورقم الهاتف
    zz = request.user
    try:
        phone_number = zz.profile.phone_number
    except AttributeError:
        return render(request, 'masha/interface.html', {"message": "لا يوجد لديك ملف تعريف صالح."})

    # التنبيهات العامة (لجميع المستخدمين)
    num_unread_3 = filter_forms(Form.objects.filter(
        show_tasrah_karoj=True,
        return_form=False,
        digital=False,
        tr_masah=False,
        exit_eng=False
    ), request.user).count()

    # كل العدادات مقيّدة بمديرية المستخدم (المدير يرى الكل)
    num_unread = filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=False), request.user).count()
    num_unread_1 = filter_reports(report_masahi.objects.filter(
        tr_masah=True,
        return_masah_jm=False,
        rafth_adarah_generl=False,
        masahi_convert=False,
        agree_adarah_generl_by_manager_mahfth=False,
        rafth_adarah_generl_by_manager_mahfth=False
    ), request.user).count()
    print_report_a = filter_reports(
        report_masahi.objects.filter(return_masah_jm=True, print_nah=False), request.user
    ).count()
    rafth_ald = filter_reports(
        report_masahi.objects.filter(rafth_adarah_generl=True), request.user
    ).count()
    num_unread_agree_mahfth = filter_reports(
        report_masahi.objects.filter(agree_adarah_generl_by_manager_mahfth=True), request.user
    ).count()
    num_unread_rafth_mahfth = filter_reports(
        report_masahi.objects.filter(rafth_adarah_generl_by_manager_mahfth=True), request.user
    ).count()

    context = {
        'num_unread': num_unread,
        'num_unread_1': num_unread_1,
        'num_unread_3': num_unread_3,
         'print_report_a': print_report_a,
         'rafth_ald':rafth_ald,
           "num_unread_agree_mahfth": num_unread_agree_mahfth,
        "num_unread_rafth_mahfth": num_unread_rafth_mahfth
    }

    return render(request, 'masha/show_manager_masah_nah.html', context)
@login_required
def show_report_nah_by_manager(request):
    print_report_x= report_masahi.objects.filter( 
             return_masah_jm=True,
            rafth_adarah_generl=False,
            masahi_convert=False,
            rafth_adarah_generl_by_manager_mahfth=False
            ) 
    context={'print_report_x':print_report_x} 
    return render(request,'masha/print_report_mashi_report_nah.html',context)
def show_report_nah_by_manager_rafth(request):
    print_report_x= report_masahi.objects.filter( rafth_adarah_generl=True) 
    context={'print_report_x':print_report_x} 
    return render(request,'masha/show_report_nah_by_manager_rafth.html',context)
def  serch_in_screen_prisdent_masah_talbt(request):
    return render(request,'masha/serch_in_screen_talbt_date.html')


@csrf_exempt
def serch_in_screen_prisdent_masah_talbt_to_data_base(request):
    if request.method == 'GET':
        # استدعاء التواريخ من الفورم
        start_date_str = request.GET.get('zz')  # تاريخ البداية
        end_date_str = request.GET.get('q')    # تاريخ النهاية

        # تحقق من أن الحقول ليست فارغة
        if not start_date_str or not end_date_str:
            messages.error(request, "يجب ألا تكون الحقول فارغة")
            return redirect(reverse('masha:serch_in_screen_prisdent_masah_talbt'))

        # تحويل النصوص إلى كائنات datetime.date
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "صيغة التاريخ غير صحيحة")
            return redirect(reverse('masha:serch_in_screen_prisdent_masah_talbt'))

        # إذا تم إدخال التواريخ بالعكس، عكسها تلقائياً
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # فلترة البيانات
        # إذا كان الحقل DateTimeField، استخدم __date__range
        form = Form.objects.filter(sent_att__date__range=(start_date, end_date))

        context = {
            'form': form,
            'start_date': start_date,
            'end_date': end_date,
        }

        return render(request, 'masha/serch_in_screen_talbt_date.html', context)
      



from django.http import JsonResponse


@mahfth_screen_required
def show_manager_masah_nah_json(request):
    user = request.user

    num_unread_3 = filter_forms(Form.objects.filter(
        show_tasrah_karoj=True,
        return_form=False,
        digital=False,
        tr_masah=False,
        exit_eng=False
    ), user).count()

    num_unread = filter_forms(
        Form.objects.filter(show_tasrah_karoj=False, rafth_maml=False, talb_astkml=False), user
    ).count()
    num_unread_1 = filter_reports(report_masahi.objects.filter(
        tr_masah=True,
        return_masah_jm=False,
        rafth_adarah_generl=False,
        masahi_convert=False,
        agree_adarah_generl_by_manager_mahfth=False,
        rafth_adarah_generl_by_manager_mahfth=False
    ), user).count()
    print_report_a = filter_reports(
        report_masahi.objects.filter(return_masah_jm=True, print_nah=False), user
    ).count()
    rafth_ald = filter_reports(
        report_masahi.objects.filter(rafth_adarah_generl=True), user
    ).count()
    num_unread_agree_mahfth = filter_reports(
        report_masahi.objects.filter(agree_adarah_generl_by_manager_mahfth=True), user
    ).count()
    num_unread_rafth_mahfth = filter_reports(
        report_masahi.objects.filter(rafth_adarah_generl_by_manager_mahfth=True), user
    ).count()
    latest_qs = filter_forms(Form.objects.all(), user)
    latest_id = latest_qs.order_by('-id').first().id if latest_qs.exists() else 0

    return JsonResponse({
        "num_unread": num_unread,
        "num_unread_1": num_unread_1,
        "num_unread_3": num_unread_3,
        "print_report_a": print_report_a,
        "rafth_ald": rafth_ald,
        "latest_id": latest_id,
        "num_unread_agree_mahfth": num_unread_agree_mahfth,
        "num_unread_rafth_mahfth": num_unread_rafth_mahfth
    })


@mahfth_screen_required
def show_report_masah_by_eng_data(request,id):
     mas=report_masahi.objects.get(id=id)
     resone=Resone.objects.all()
     
     f=Shift_form_hadod.objects.filter(report_masahi=mas)
     context={'mas':mas,'f':f,'resone':resone}
     return render(request,'masha/show_report_masah_by_eng_data.html',context)
@mahfth_screen_required
def show_report_adrah(request,id):
     mas=report_masahi.objects.get(id=id)
     f=Shift_form_hadod.objects.filter(report_masahi=mas)
     context={'mas':mas,'f':f}
     return render(request,'masha/show_report_adrah.html',context)
def masahi_convert(request,id):
        masahi_convert=request.POST.get('masahi_convert')
        if   masahi_convert=='منجزة':
            masahi_convert=True
        else :
                    masahi_convert=False
        xx=masahi_convert
        form,created=report_masahi.objects.get_or_create(id=id)
        form.masahi_convert=xx
        form.save()
        return HttpResponseRedirect(reverse('masha:agree_rafth_report_masah_nah_tamp',))





def send_sms_safe(phone, message):
    """
    إرسال رسالة SMS بأمان:
    - يتحقق من وجود الإنترنت قبل الإرسال
    - يتجاهل أي خطأ إذا لم يكن هناك إنترنت
    """
    mobile_number = f"00967{phone}"
    url = "https://sms.alawaeltec.com/MainServlet"
    params = {
        "orgName": "Demosms",
        "userName": "Galsupye",
        "password": "Galsupye@17777789",
        "mobileNo": mobile_number,
        "text": message,
        "coding": "2"
    }

    try:
        # تحقق من الإنترنت
        requests.get("https://www.google.com", timeout=3)

        # إرسال الرسالة
        response = requests.get(url=url, params=params, timeout=5)
        if response.status_code == 200:
            print("SMS message sent successfully!")
        else:
            print(f"Failed to send SMS message. Error code: {response.status_code}")
    except RequestException:
        # تجاهل أي خطأ إذا لا يوجد إنترنت أو حدث فشل في الطلب
        print("No internet connection or failed to send SMS. Ignored.")


@csrf_exempt
def agree_report_masahi_by_manager_mangmant(request, id):
    exit_action = request.POST.get('exit')
    no_salm_5 = request.POST.get('no_salm_5', '')
    resone_report_stop = request.POST.get('resone_report_stop', '')
    text_36 = request.POST.get('text36', '')


    try:
        report = report_masahi.objects.get(id=id)
    except report_masahi.DoesNotExist:
        return HttpResponse("Report not found", status=404)

    form_instance = report.form

    if exit_action == 'منجزة':
        report.return_masah_jm = True
        report.masahi_convert = False
        report.ajaml=text_36
        report.save()

        # إرسال رسالة SMS فقط إذا الحالة منجزة
        phone = form_instance.phone  # رقم الهاتف من form
        message = f"رقم تقريرك المساحي هو {report.id}"
        send_sms_safe(phone, message)

    elif exit_action == 'الادارة':
        report.masahi_convert = True
        report.save()
    elif exit_action.strip() == 'رفض':
        report.rafth_adarah_generl = True
        ff=Resone.objects.get(id=resone_report_stop)
        report.resone=ff


       
        report.resone_refth=no_salm_5

        report.save()
    else:
        return HttpResponse("Invalid action", status=400)

    return HttpResponse(status=200)



@csrf_exempt
@mahfth_screen_required
def agree_report_masahi_by_manager_mangmant_adarah(request, id):
    exit_action = request.POST.get('exit')
    no_salm_5 = request.POST.get('no_salm_5', '')
    text_36 = request.POST.get('text36', '')

    try:
        report = report_masahi.objects.get(id=id)
    except report_masahi.DoesNotExist:
        return HttpResponse("Report not found", status=404)

    form_instance = report.form

    if exit_action == 'منجزة':
        report.agree_adarah_generl_by_manager_mahfth = True
        report.masahi_convert = False
        report.ajaml=text_36


    elif exit_action.strip() == 'رفض':
        report.rafth_adarah_generl_by_manager_mahfth = True
        report.masahi_convert = False
        report.resone_refth_adrah=no_salm_5
    else:
        return HttpResponse("Invalid action", status=400)

    report.save()
    return HttpResponse(status=200)
      
def rafth_agree_report_masahi_by_manager_mangmant_report_masahi_by_manager_mangmant(request,id):
     resone_refth=request.POST['resone_refth']
     rafth_adarah_generl=request.POST.get('rafth_adarah_generl')
     if     rafth_adarah_generl=='رفض':
               rafth_adarah_generl=True
     else :
               rafth_adarah_generl=False
     xx=rafth_adarah_generl
     rafth,created=report_masahi.objects.get_or_create(id=id)
     rafth.rafth_adarah_generl=True
     rafth.resone_refth=resone_refth
     rafth.save()
     return HttpResponseRedirect(reverse('masha:agree_rafth_report_masah_nah_tamp',))
@csrf_exempt
def red_bol_massage(request):
    number=request.POST['number']
    red_mas=request.POST['red_mas']
    
    
    


    exit=request.POST.get('exit')
    if     exit=="منجزة" :
               exit=True
    else :
               exit=False
    x=exit
    a,created=Conection.objects.get_or_create(id=number)
    a.red_bol=x
    a.red=red_mas
    message = f"  {red_mas}"
    mobile_number = f"00967{a.phone}"
    url = "https://sms.alawaeltec.com/MainServlet"
    params = {"orgName": "Demosms",
        "userName": "Galsupye",
        "password": "Galsupye@17777789",
        "mobileNo": mobile_number,
        "text": message,
        "coding": "2"}
    response = requests.get(url=url, params=params)
    if response.status_code == 200:
            print("SMS message sent successfully!")
    else:
             print(f"Failed to send SMS message. Error code: {response.status_code}")

    a.save()
    return HttpResponse(status=200)


@mahfth_screen_required
def asder_nah_report_masah(request):
    return render(request,'masha/asder_nah_report_masah.html')
@mahfth_screen_required
def asder_report_masah_db_nah_project(request):
    if 'q' in request.GET:
        q=request.GET['q']
        if q == "" or not q.isdigit():
                            messages.success(request,"يجب ان لايكون الحقل فارغ ويجب ان يحتوي على عدد صحيح" ) 
                            return HttpResponseRedirect(reverse('masha:asder_nah_report_masah'))
        else:
            f,created=report_masahi.objects.get_or_create(id=q)
            if f.return_masah_jm==True:
                form=Shift_form_hadod.objects.filter(report_masahi=f)[0:1]
                context={'form':form,'f':f}
                return render(request,'masha/asder_nah_report_masah.html',context)
            else:
                       return render(request,'masha/asder_nah_report_masah.html')



import os
import base64
import mimetypes
import pdfkit

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template

from .models import Form

def image_to_base64(image_path):

    try:

        if not os.path.isfile(image_path):
            print("الصورة غير موجودة:", image_path)
            return ""

        with open(image_path, "rb") as image_file:

            encoded = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        mime_type, _ = mimetypes.guess_type(
            image_path
        )

        if not mime_type:
            mime_type = "image/jpeg"

        return (
            f"data:{mime_type};base64,{encoded}"
        )

    except Exception as e:

        print("خطأ في الصورة:", e)

        return ""







    # ========================================================
    # الصورة الثابتة
    # ========================================================


    # ========================================================
    # Context
    # ========================================================

    # ========================================================
    # العثور على wkhtmltopdf
    # ========================================================

   

        

@login_required
def show_managmant_masah(request)  :
    role_landing = role_landing_url(request.user)
    if role_landing:
        return redirect(role_landing)
    num_unread =Form.objects.filter(tr_masah=False,show_tasrah_karoj=True).count()
    context={'num_unread':num_unread}
    return render(request,'masha/show_managmant_masah.html',context)
    
@space_roles_only(block_management=True)
@mahfth_screen_required
def show_managment_nah(request):
    return render(request,'masha/show_managment_nah.html')
@mahfth_screen_required
def werd_sader_manager(request):
    return render(request,'masha/werd_sader_manager.html')
@space_roles_only(block_management=True)
@mahfth_screen_required
def screen_adrat_ver(request):
    num_unread =Conection.objects.filter().count()
    num_unread_1 =report_masahi.objects.filter(masahi_convert=True,convert_agin=False,convert_agin_agree=False,agree_adarah_generl_by_manager_mahfth=False,rafth_adarah_generl_by_manager_mahfth=False).count()
    num_unread_agree=report_masahi.objects.filter(agree_adarah_generl_by_manager_mahfth=True,rafth_adarah_generl_by_manager_mahfth=False).count()
    num_unread_rafth =report_masahi.objects.filter(rafth_adarah_generl_by_manager_mahfth=True).count()
    context={'num_unread':num_unread,'num_unread_1':num_unread_1,'num_unread_agree':num_unread_agree,'num_unread_rafth':num_unread_rafth}
    return render(request,'masha/show_managment_nah.html',context)
@space_roles_only(block_management=True)
@mahfth_screen_required
def get_realtime_counts(request):
    num_unread = Conection.objects.filter().count()
    num_unread_1 = report_masahi.objects.filter(
        masahi_convert=True,
        convert_agin=False,
        convert_agin_agree=False,
        agree_adarah_generl_by_manager_mahfth=False,
        rafth_adarah_generl_by_manager_mahfth=False

    ).count()
    num_unread_agree =report_masahi.objects.filter(agree_adarah_generl_by_manager_mahfth=True,rafth_adarah_generl_by_manager_mahfth=False).count()
    num_unread_rafth =report_masahi.objects.filter(rafth_adarah_generl_by_manager_mahfth=True).count()

    return JsonResponse({
        "num_unread": num_unread,
        "num_unread_1": num_unread_1,
        "num_unread_agree":num_unread_agree,
        "num_unread_rafth":num_unread_rafth

    })
@login_required
def screen_paesdint_masah(request):
    role_landing = role_landing_url(request.user)
    if role_landing:
        return redirect(role_landing)
    return render(request,'masha/show_managmant_masah.html')
@mahfth_screen_required
def screen_interface_line_tslime_nah(request):
        return render(request,'masha/screen_interface_line_tslime_nah.html')
@mahfth_screen_required
def add_tlab_tslime_line_organzatio_add_db(request):
    x=Mahther_line.objects.first()
    try:

        

        
        Shift_streatrFormSet = formset_factory(
            Shift_streatrForm,
    extra=1,  # Adds one empty form by default
    min_num=3,  # Requires the user to fill out at least 4 forms
    validate_min=True  # Ensures the minimum number of forms is met
)
        if request.method == 'POST':
            number=request.POST['number']

            formset = Shift_streatrFormSet(request.POST)
            if not formset.is_valid():
                return render(request, 'masha/add_tlab_tslime_line_organzation.html', {'formset': formset, 'errors': formset.errors, 'x': x})
            else:
                
        
                for form in formset:
                    if form.cleaned_data:

                        
                        Shift_streatr = form.save(commit=False)
                        Shift_streatr.mahther_line = x
                        if form.cleaned_data['shar_atjah'] == "شارع":
                            m = form.cleaned_data['type_street']
                            y = form.cleaned_data['width_street']
                            z=form.cleaned_data['number_strate']
                            streat=Streat.objects.create(type_street=m,width_street=y,mahther_line=x,number_strate=z)               
                        Shift_streatr.save()
                return redirect('masha:screen_enter_number_mahther_and_number_strate_and_unit')
        else:
             formset =Shift_streatrFormSet(initial=[{'mahther_line':x.id}] )
             return render(request, 'masha/add_tlab_tslime_line_organzation.html', {'x':x,'formset': formset})
    except Form.DoesNotExist:
        return HttpResponse('shift_form_hadod not found', status=404)
    
    return render(request,'masha/add_tlab_tslime_line_organzation.html',context)
@mahfth_screen_required
def add_tlab_tslime_line_organzatio_add_db_strate(request):

 
    sh_1=request.POST.getlist('chk')
    val=request.POST['shml_2']
    
    
    

    val_1=request.POST['jan_2']
    val_2=request.POST['shar_2']
    val_3=request.POST['gr_2']
    w_1=request.POST['lab_dd']
    w_2=request.POST['id_w_2']
    w_3=request.POST['lab_dddddd']
    w_4=request.POST['lab_jj'] 
    w_5=request.POST['id_w_5']
    w_6=request.POST['lab_jjjjjj']
    w_7=request.POST['lab_ss']
    w_8=request.POST['id_w_8'] 
    w_9=request.POST['lab_ssssss']
    w_10=request.POST['lab_gg']
    w_11=request.POST['id_w_11']
    w_12=request.POST['lab_gggggg'] 
    shml_11=request.POST['shml_11']
    shml_22=request.POST['shml_22']
    shml_33=request.POST['shml_33']
    shml_44=request.POST['shml_44']
    

    number_str=request.POST['number_str']
    width_srt=request.POST['width_srt']

    

    

    
    

        

    

            
    for i in  sh_1:
        if i=="شمال" :
            
            shift_form_hadod=Shift_streatr.objects.create(streat=st,sh=i,quantity=val,shar_atjah=shml_11,width_street=w_1,type_street=w_2,  number_strate=w_3)
        elif i=="جنوب" :
            
            shift_form_hadod=Shift_streatr.objects.create(streat=st,sh=i,quantity=val_1,shar_atjah=shml_22,width_street=w_4,type_street=w_5,  number_strate=w_6)
        elif i=="شرق" :
            
            shift_form_hadod=Shift_streatr.objects.create(streat=st,sh=i,quantity=val_2,shar_atjah=shml_33,width_street=w_7,type_street=w_8,  number_strate=w_9)
        elif i=="غرب" :
            
            shift_form_hadod=Shift_streatr.objects.create(streat=st,sh=i,quantity=val_3,shar_atjah=shml_44,width_street=w_10,type_street=w_11,  number_strate=w_12)

    
    


def add_tlab_tslime_line_organzatio_add_strate_and_unit_to_data_base(request):
    eng_first = request.POST.get('eng_first', '')
    eng_second = request.POST.get('eng_second', '')
    eng_ther = request.POST.get('eng_ther', '')
    img_mahther = request.FILES.get('img_mahther', None)
    hid_gata = request.POST.get('hid_gata')

    uni = Unit.objects.get(id=hid_gata)
    
    xx = Mahther_line.objects.create(
        eng_1 = eng_first,
        eng_2 = eng_second,
        eng_resive = eng_ther,
        unit = uni,
        mahther_line_nah = img_mahther
    )

    messages.success(request, f"تمت إضافة المحضر رقم {xx.id}")
    return HttpResponseRedirect(reverse('masha:add_tlab_tslime_line_organzatio_add_db'))

@mahfth_screen_required
def show_center(request):
    mahf=visible_mahfth_list(request.user)
    context={'mahf':mahf}
    return render(request,'masha/show_center.html',context)
@mahfth_screen_required
def show_erea_masha(request,id):
    mahf=Mahfth.objects.get(id=id)
    erea11=Erea.objects.filter(mahfth=mahf)
    context={'erea11':erea11,'mahf':mahf}
    return render(request,'masha/show_erea_masha.html',context)
@mahfth_screen_required
def show_gata_masha(request,id):
     erea=Erea.objects.get(id=id)
     gata=Gata.objects.filter(erea=erea)
     context={'gata':gata,'erea':erea}
     return render(request,'masha/show_gata_masha.html',context)
@mahfth_screen_required
def show_unit_masha(request,id):
     g=Gata.objects.get(number=id)
     unit11=Unit.objects.filter(gata=g)
     context={'unit11':unit11,'g':g}
     return render(request,'masha/show_unit_masha.html',context)
@mahfth_screen_required
def show_strate_masha_mahter(request,id):
    uu=Unit.objects.get(id=id)
    aa=Mahther_line.objects.filter(unit=uu)
    context={'aa':aa,'uu':uu}
    return render(request,'masha/show_strate_unit_nah.html',context)
@mahfth_screen_required
def show_strate_masha_hadod_information(request,id):
    xx=Streat.objects.get(id=id)
    yy=Shift_streatr.objects.filter(streat=xx)
    context={'yy':yy}
    return render(request,'masha/show_atjah_strate_line_nah.html',context)
@mahfth_screen_required
def enter_face_enter_nah(request):
    user = request.user

    # العداد مقيّد بمديرية المستخدم (المدير يرى كل المديريات)
    num_unread_3 = filter_forms(Form.objects.filter(
        show_tasrah_karoj=True,
        return_form=False,
        digital=False,
        tr_masah=False,
        exit_eng=False
    ), user).count()

    context = {
        'num_unread_3': num_unread_3,
    }
    return render(request, "masha/enter_face_enter_nah.html", context)

   



# ============================
# الدوال الموحدة
# ============================

# ============================================================
# Imports
# ============================================================

import os
import sys
import base64
import mimetypes
import pdfkit

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template


# ============================================================
# تحويل الصورة إلى Base64
# ============================================================


def add_form_new_talb(request):
    form=Form.objects.first()
    context={'form':form}



    WKHTMLTOPDF_CMD = r'C:\wkhtmltopdf\bin\wkhtmltopdf.exe'
    pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)

    template = get_template('masha/number_form.html')
    html = template.render(context)
    pdf_file = pdfkit.from_string(html, False)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    response.write(pdf_file)
    return response


@space_roles_only(block_management=True)
@mahfth_screen_required
def screen_enter_number_mahther_and_number_strate_and_unit(request):
    mah=visible_mahfth_list(request.user)
    
    st=Streat.objects.last()

    context={'mah':mah,'st':st}
    return render(request,'masha/screen_enter_number_mahther_and_number_strate_and_unit.html',context)
def map(request):
    if request.method == "POST":
        latitude = float(request.POST['point_1'])
        longitude = float(request.POST['point_2'])
        name = request.POST['name']
        location = Location(latitude=latitude, longitude=longitude, name=name)
        location.save()
        map_obj = folium.Map(location=[latitude, longitude], zoom_start=13)
        folium.Marker(
        location=[latitude, longitude],
        popup=f"{name}<br>",
    ).add_to(map_obj)
    locations = Location.objects.all()
    for location in locations:
        folium.Marker(
            location=[location.latitude, location.longitude],
            popup=f"{location.name}<br>",
        ).add_to(map_obj)
    map_html = map_obj.get_root().render()
    context = {'map_html': map_html}
    return render(request, 'masha/map.html', context)
        
def map_add_data_base(request):
    return render(request, 'masha/map_add_data_base.html')

#@user_passes_test(lambda u: u.is_superuser or u.has_perm('masha.add_shift_form_hadod'))    





from django.shortcuts import render, get_object_or_404, redirect
from django.forms import formset_factory
from .forms import Shift_form_hadodForm, BaseShiftFormSet
from .models import Shift_form_hadod, Form, report_masahi

def add_locatios_shift_to_report_masah(request, id):
    xx = get_object_or_404(Form, id=id)

    ShiftFormSet = formset_factory(
        Shift_form_hadodForm,
        formset=BaseShiftFormSet,
        extra=1,
        min_num=3,
        validate_min=True
    )

    if request.method == 'POST':
        formset = ShiftFormSet(request.POST)

        # إذا الفورمسيت غير صالح، عرض الفورمسيت مع الأخطاء
        if not formset.is_valid():
            return render(
                request,
                'masha/add_locatios_shift_to_report_masah.html',
                {'formset': formset, 'xx': xx}
            )

        # الحصول على أو إنشاء تقرير المساحي
        mas, created = report_masahi.objects.get_or_create(name="مساحي", form=xx)
        existing_shifts = list(Shift_form_hadod.objects.filter(form=xx, report_masahi=mas))

        for i, form in enumerate(formset):
            if not form.cleaned_data:
                continue  # تجاهل الصفوف الفارغة

            data = form.cleaned_data
            shar = data.get('shar_atjah')
            number_strate = data.get('number_strate')

            # رقم الشارع مطلوب فقط إذا الخيار "شارع"
            if shar and shar.strip() == 'شارع':
                if not number_strate or number_strate.strip() == '':
                    continue  # خطأ موجود في الفورمسيت، لا نحفظ هذا الصف
                number_strate = number_strate.strip()
            else:
                number_strate = ''  # لتجنب IntegrityError إذا لم يكن شارع

            # عرض الشارع: فقط إذا أدخل المستخدم قيمة جديدة
            width_value = data.get('width_street')
            if width_value in [None, '']:
                width_value = None  # لن يتم حفظ None، القيمة القديمة تبقى

            # تحديث الصفوف الموجودة إذا رقم الاستمارة ورقم التقرير موجود
            shift_instance = None
            if i < len(existing_shifts):
                candidate = existing_shifts[i]
                if candidate.form == xx and candidate.report_masahi == mas:
                    shift_instance = candidate

            if shift_instance:
                # تحديث كامل الصف بالقيم الجديدة
                shift_instance.number_strate = number_strate
                shift_instance.type_street = data['type_street']
                shift_instance.width_street = data['width_street']
                shift_instance.shar_atjah = shar
                shift_instance.quantity = data['quantity']
                shift_instance.sh = data['sh']
                if width_value is not None:
                    shift_instance.width_street = width_value
                shift_instance.save()
            else:
                # إنشاء صف جديد
                create_data = {
                    'form': xx,
                    'report_masahi': mas,
                    'number_strate': number_strate,
                    'type_street': data['type_street'],
                    'shar_atjah': shar,
                    'quantity': data['quantity'],
                    'sh': data['sh']
                }
                if width_value is not None:
                    create_data['width_street'] = width_value
                Shift_form_hadod.objects.create(**create_data)

        # تحديث eraa_asqt مباشرة في جدول Form
        aa = xx.get_qunit
        mm = xx.get_street
        zz = xx.get_street_big
        if aa is not None and mm is not None:
            Form.objects.filter(id=xx.id).update(
                erea_asqt=aa,
                width_street_big=mm,
                width_street_big_not=zz
            )

        return redirect('masha:astkmal_report_masah_nah', id=xx.id)

    else:
        formset = ShiftFormSet(initial=[{'form': xx.id}])
        return render(
            request,
            'masha/add_locatios_shift_to_report_masah.html',
            {'xx': xx, 'formset': formset}
        )
from django.shortcuts import render, get_object_or_404

def show_form_shifts(request, id):
    form_obj = get_object_or_404(Form, id=id)

    mas, created = report_masahi.objects.get_or_create(
        name="مساحي",
        form=form_obj
    )

    shifts = Shift_form_hadod.objects.filter(
        form=form_obj,
        report_masahi=mas
    )

    return render(
        request,
        'masha/show_form_shifts.html',
        {
            'form_obj': form_obj,
            'shifts': shifts
        }
    )
@mahfth_screen_required
def serch_data_report_mashi_to_update(request):
    return render(
            request,
            'masha/serch_data_report_mashi_to_update.html',
           
        )
from django.forms import modelformset_factory
@mahfth_screen_required
def edit_form_shifts(request, id):
    form_obj = get_object_or_404(Form, id=id)

    # السماح فقط إذا tr_masah=False
    mas = report_masahi.objects.filter(
        name="مساحي",
        form=form_obj,
        tr_masah=False
      
    ).first()

    if not mas:
        messages.error(request, "لا يمكن التعديل على هذا السجل لأن التقرير تم اعتماده أو ترحيله سابقاً.")
        return redirect('masha:serch_data_report_mashi_to_update')

    ShiftFormSet = modelformset_factory(
        Shift_form_hadod,
        form=Shift_form_hadodForm,
        extra=0
    )

    queryset = Shift_form_hadod.objects.filter(
        form=form_obj,
        report_masahi=mas
    )

    if request.method == 'POST':
        formset = ShiftFormSet(
            request.POST,
            queryset=queryset,
            form_kwargs={
                'form_instance': form_obj,
                'report_instance': mas
            }
        )

        if formset.is_valid():
            formset.save()

            aa = form_obj.get_qunit
            mm = form_obj.get_street

            if aa is not None and mm is not None:
                Form.objects.filter(id=form_obj.id).update(
                    erea_asqt=aa,
                    width_street_big=mm
                )

            messages.success(request, "تم حفظ التعديلات بنجاح ✅")
            return redirect('masha:astkmal_report_masah_nah', id=form_obj.id)

    else:
        formset = ShiftFormSet(
            queryset=queryset,
            form_kwargs={
                'form_instance': form_obj,
                'report_instance': mas
            }
        )

    return render(request, 'masha/edit_form_shifts.html', {
        'form_obj': form_obj,
        'formset': formset
    })
from django.forms import modelformset_factory
@mahfth_screen_required
def edit_form_shifts_nah(request,id):
        form_obj = get_object_or_404(Form, id=id)
        
        res=Resone.objects.get(id=1)
        mas = report_masahi.objects.filter(name="مساحي",form=form_obj,tr_masah=True,rafth_adarah_generl=True,resone=res).first()
        flas=mas.id
        if not mas:
            messages.error(request, "لا يمكن التعديل على هذا السجل لأن التقرير تم اعتماده أو ترحيله سابقاً.")
            return redirect('masha:serch_data_report_mashi_to_update')
        ShiftFormSet = modelformset_factory(Shift_form_hadod,form=Shift_form_hadodForm,extra=0 )
        queryset = Shift_form_hadod.objects.filter(form=form_obj, report_masahi=mas)
        if request.method == 'POST':
            formset = ShiftFormSet(
            request.POST,
            queryset=queryset,
            form_kwargs={
                'form_instance': form_obj,
                'report_instance': mas})
            if formset.is_valid():
                formset.save()

                aa = form_obj.get_qunit
                mm = form_obj.get_street
                if aa is not None and mm is not None:
                    Form.objects.filter(id=form_obj.id).update(erea_asqt=aa,width_street_big=mm)
                    messages.success(request, "تم حفظ التعديلات بنجاح ✅")
                    report,created=report_masahi.objects.get_or_create(id=flas)
                    report.rafth_adarah_generl=False
                    report.save()

                    return redirect('masha:show_astmrat')
        else:
                formset = ShiftFormSet(queryset=queryset,form_kwargs={'form_instance': form_obj,'report_instance': mas})
                return render(request, 'masha/adit_form_shift_update_nah.html', {'form_obj': form_obj,'formset': formset})
def map_project(request,id):
    ss= Form.objects.get(id=id)
    locations = Location.objects.filter(form=ss)
    m = folium.Map(location=[15.369445, 44.191006], zoom_start=9)
    latitudes = []
    longitudes = []
    location_names = []
    center_latitude = sum(location.latitude for location in locations) / len(locations)
    center_longitude = sum(location.longitude for location in locations) / len(locations)
    center = [center_latitude, center_longitude]
    m = folium.Map(location=center, zoom_start=13)
    latitudes = []
    longitudes = []
    location_names = []
    for location in locations:
        latitudes.append(location.latitude)
        longitudes.append(location.longitude)
        location_names.append(location.name)
    FastMarkerCluster(data=list(zip(latitudes, longitudes,location_names))).add_to(m)
    folium.Circle(
        location=center,
        radius=1000,
        color="#3186cc",
        fill=True,
        fill_color="#3186cc",
        tooltip=location_names).add_to(m)
    for lat, lng in zip(latitudes, longitudes):
        folium.Circle(
         location=[lat, lng],
         radius=50,
         color="#ff0000",
         fill=True,
         fill_color="#ff0000").add_to(m)
    minimap=MiniMap()
    m.add_child(minimap)
    map_html = m.get_root().render()
    context = {'map_html': map_html}
    return render(request, 'masha/map_project.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import verificationForm
from .models import Valdtion, Conection

@login_required
def interface(request):
    # ----- نطاق المستخدم (مدينة/مديرية) -----
    # المستخدم العادي يرى فقط روابط الأقسام المرتبطة بمدينته/مديريته،
    # ومدير النظام يرى كل الأقسام.
    from .scoping import get_user_city_name, get_user_mahfth

    my_city_name = get_user_city_name(request.user)
    has_mahfth_access = bool(get_user_mahfth(request.user) or my_city_name)
    scope_context = {
        "my_city_name": my_city_name,
        "has_mahfth_access": has_mahfth_access,
    }

    if request.method == "POST":
        form = verificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['verification_code']
            v = Valdtion.objects.filter(verification_code=code).first()

            if v:
                # إنشاء السجل في Conection
                Conection.objects.create(name=v.name, phone=v.phone, verification_code=code)
                return redirect('masha:interface')  # إعادة توجيه بعد نجاح العملية
            else:
                # إضافة خطأ للمستخدم
                form.add_error('verification_code', 'رمز التحقق غير صحيح')

        # لو هناك أخطاء، نرجع النموذج مع الأخطاء
        scope_context['form'] = form
        response = render(request, 'masha/interface.html', scope_context)

    else:
        # GET request
        form = verificationForm()
        scope_context['form'] = form
        response = render(request, 'masha/interface.html', scope_context)

    # ----- إضافة حماية من الرجوع بعد logout -----
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


def select_erea_mderah_masha(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        selected_option = data['selected_option']
        if Unit.objects.filter(mahfth__id=selected_option).exists():
            x =Mahfth.objects.get(id=selected_option)
            salm = Unit.objects.filter(mahfth__id=selected_option)
            my_model_json = serializers.serialize('json', salm)
        else:
            my_model_json = json.dumps({'field_name': 'شركة'})
        return JsonResponse(my_model_json, safe=False)
def select_gata_erea_mderah_masha(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        selected_option = data['selected_option']
        if Gata.objects.filter(erea__id=selected_option).exists():
            x =Erea.objects.get(id=selected_option)
            salm = Gata.objects.filter(erea__id=selected_option)
            my_model_json = serializers.serialize('json', salm)
        else:
            my_model_json = json.dumps({'field_name': 'شركة'})
        return JsonResponse(my_model_json, safe=False)
def select_unit_masha(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        selected_option = data['selected_option']
        if Unit.objects.filter(gata__id=selected_option).exists():
            x =Gata.objects.get(id=selected_option)
            salm = Unit.objects.filter(gata__id=selected_option)
            my_model_json = serializers.serialize('json', salm)
        else:
            my_model_json = json.dumps({'field_name': 'شركة'})
        return JsonResponse(my_model_json, safe=False)
@csrf_exempt
def sand_connections(request):
    if request.method=="POST":
        comments=request.POST['comments']
        phone=request.POST['phone']
        name=request.POST['name']
        verification_code=str(random.randint(100000,999999))
        x=Valdtion.objects.create(name=name,phone=phone,massage=comments,verification_code=verification_code)
        message = f"   رقم التحقق الخاص بك هو {verification_code}"
        phone = f"00967{phone}"
        url = "https://sms.alawaeltec.com/MainServlet"
        params = {"orgName": "Demosms",
        "userName": "Galsupye",
        "password": "Galsupye@17777789",
        "mobileNo": phone,
        "text": message,
        "coding": "2"}
    response = requests.get(url=url, params=params)

    if response.status_code == 200:
            print("SMS message sent successfully!")
    else:
             print(f"Failed to send SMS message. Error code: {response.status_code}")
    return HttpResponseRedirect(reverse('masha:verify_code_insert',))
def verify_code_insert(request):
    form=verificationForm()
    return render(request,'masha/ver.html',{'form':form})
def red_bol(request,id) :

    f=Conection.objects.get(id=id)
    context={'f':f}
    return render(request,'masha/red_bol.html',context)

@space_roles_only(block_management=True)
def show_conecctions(request):
    conection=Conection.objects.filter(red_bol=False)
    context={'conection':conection}
    return render(request, 'masha/massage.html', context)
def add_location(request,id):
    if request.method == "POST":
        form = Location_UtmForm(request.POST)
        if form.is_valid():
                   f=Form.objects.get(id=id)
                   location_instance = form.save(commit=False)  # حفظ النموذج بدون حفظه في قاعدة البيانات
                   location_instance.form = f 
                   form.save()
                   return redirect('masha:agree_tsrah_xx')  # قم بتعديل الرابط حسب الحاجة
    else:
        form = Location_UtmForm()
    return render(request, 'masha/add_location_Utm.html', {'form': form})
def location_list(request,id):
  r=Form.objects.get(id=id)
  locations=Location_Utm.objects.filter(form=r)
  context={'locations':locations}
  return render(request, 'masha/location_list.html',context)

def show_tsrah_exit_eng_by_manger (request):
    

    form=Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
    context={'form':form}
    return render(request,'masha/show_tsrah_exit_eng_by_manger.html',context)
def show_tsrah_exit_eng_by_manger_by_manger(request):
    form=Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=False).order_by('-id')
    context={'form':form}
    return render(request,'masha/show_tsrah_exit_eng_by_presdent_mashi.html',context)

def live_search_ajax_tsrah_exit_tsrah_karoj(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) 

        matches = Form.objects.filter(
            filters,
           show_tasrah_karoj=True
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "streat_name": obj.streat_name,
                "name_documnt": obj.name_documnt,
               
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
               
            })

    return JsonResponse({"results": results})
    
def show_tsrah_exit_eng_by_manger_report (request):
    

    form=Form.objects.filter(show_tasrah_karoj=True,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
    context={'form':form}
    return render(request,'masha/reprt_tsrah_exit_nah_by_bana.html',context)
def live_search_tsrah_bana_report(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) 

        matches = Form.objects.filter(
            filters,
            show_tasrah_karoj=True,
           hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "streat_name": obj.streat_name,
               
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
               
            })

    return JsonResponse({"results": results})
 


from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import Form

# الصفحة الرئيسية لعرض التصاريح
def show_tsrah_exit_eng_by_manger_report_astshrah(request):
    forms = Form.objects.filter(
        show_tasrah_karoj=True,
        hidden_ansh_hdm="استشارة"
    ).order_by('-id')
    context = {'forms': forms}
    return render(request, 'masha/report_tsrah_nah.html', context)

# دالة البحث اللحظي
def live_search_tsrah_exit(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) 

        matches = Form.objects.filter(
            filters,
            show_tasrah_karoj=True,
            hidden_ansh_hdm="استشارة"
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "streat_name": obj.streat_name,
               
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
               
            })

    return JsonResponse({"results": results})


from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden

def is_admin_or_has_permission(user):
    return user.is_superuser or user.has_perm("masha.add_form")

@coordinator_or_manager_required
@login_required
def astshr(request):
    # الوصول مسموح للمدير أو لمستخدم مرتبط بمدينة/مديرية،
    # والبيانات (المديرية) مقيّدة في القالب وscoping.
    if not can_access_mahfth_screen(request.user):
        return HttpResponseForbidden("ليس لديك الصلاحية للوصول إلى هذه الصفحة.")

    ty = typ.objects.all()
    type_s = Type_talb_astshr.objects.all()
    typ_t = Type_talb.objects.all()
    saf = Safah.objects.all()
    val = Vald_doc.objects.all()
    val_m = Vald_tharb.objects.all()
    ass = get_object_or_404(AStmrah, id=2)
    zz = request.user

    mah = visible_mahfth_list(request.user)

    context = {
        'mah': mah,
        'ty': ty,
        'zz': zz,
        'type_s': type_s,
        'typ_t': typ_t,
        'saf': saf,
        'ass': ass,
        'val': val,
        'val_m': val_m
    }

    return render(request, 'masha/astshr.html', context)


    
    

    

def verify_code(request):
    if request.method=="POST":
        form=verificationForm(request.POST)
        if form.is_valid():
            
            code=form.cleaned_data['verification_code']
            v=Valdtion.objects.get(verification_code=code)
            vald,created=Valdtion.objects.get_or_create(verification_code=code)
            m=vald.massage
        

            name=vald.name
            phone=vald.phone
            con,created=Conection.objects.get_or_create(name=name,phone=phone,valdtion=vald,massage=m)
            con.save()
        
            if v :

                return redirect('masha:interface')
            else:
                form.add_error('verification_code','رمز  التحقق غير صحيح')
    else:
        form=verificationForm()
        return render(request,'masha/interface.html',{'form':form})
def convert_agin_agree(request,id):
        convert_agin_agree=request.POST.get('convert_agin_agree')
        if   convert_agin_agree=='منجزة':
            convert_agin_agree=True
        else :
                    convert_agin_agree=False
        xx=convert_agin_agree
        form,created=report_masahi.objects.get_or_create(id=id)
        form.convert_agin_agree=xx
        form.save()

        return HttpResponseRedirect(reverse('masha:show_convert_to_mashi_from_fero',))
def convert_agin(request,id):
     resone_refth_adrah=request.POST['resone_refth_adrah']
     convert_agin=request.POST.get('convert_agin')
     if     convert_agin=='رفض':
               convert_agin=True
     else :
               convert_agin=False
     xx=convert_agin
     rafth,created=report_masahi.objects.get_or_create(id=id)
     rafth.convert_agin=xx
     rafth.resone_refth_adrah=resone_refth_adrah
     rafth.save()
     return HttpResponseRedirect(reverse('masha:show_convert_to_mashi_from_fero',))
from django.shortcuts import render, redirect, get_object_or_404
from .models import Mahfth, Erea, Gata, Eng, Unit
from .forms import MahfthForm, EreaForm, GataForm, EngForm, UnitForm

# ====== Mahfth ======
@login_required
def index(request):
    """لوحة التحكم: المستخدم العادي يرى بيانات مديريته فقط، والمدير يرى الكل."""
    from django.db.models import Count

    user = request.user
    my_mahfth = get_user_mahfth(user)
    is_manager = user.is_superuser or user.is_staff

    forms_qs = Form.objects.all()
    reports_qs = report_masahi.objects.all()
    if not is_manager:
        if my_mahfth is None:
            forms_qs = forms_qs.none()
            reports_qs = reports_qs.none()
        else:
            forms_qs = forms_qs.filter(mahfth=my_mahfth)
            reports_qs = reports_qs.filter(form__mahfth=my_mahfth)

    mahfth_stats = (
        visible_mahfth_list(user)
        .annotate(forms_count=Count("form", distinct=True))
        .order_by("name")
    )

    latest_forms = forms_qs.select_related("mahfth", "typ").order_by("-id")[:10]
    latest_reports = (
        reports_qs.select_related("form", "form__mahfth").order_by("-id")[:10]
    )

    context = {
        "my_mahfth": my_mahfth,
        "is_manager": is_manager,
        "mahfth_stats": mahfth_stats,
        "latest_forms": latest_forms,
        "latest_reports": latest_reports,
        "forms_total": forms_qs.count(),
        "reports_total": reports_qs.count(),
        "users_total": User.objects.count() if is_manager else 0,
        "mahfth_total": mahfth_stats.count(),
    }
    return render(request, "masha/index.html", context)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Mahfth
from .forms import MahfthForm

# عرض الصفحة مع الفورم والجدول
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def mahfth_list(request):
    items = Mahfth.objects.all().order_by('-id')
    form = MahfthForm()
    return render(request, 'masha/add_to_data_base_mahfth.html', {
        'items': items,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def mahfth_create(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        if item_id:
            item = get_object_or_404(Mahfth, pk=item_id)
            form = MahfthForm(request.POST, instance=item)
        else:
            form = MahfthForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def mahfth_delete(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        item = get_object_or_404(Mahfth, pk=pk)
        item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def erea_list(request):
    items = Erea.objects.all().order_by('-id')
    form = EreaForm()
    return render(request, 'masha/add_to_data_base_erea.html', {
        'items': items,
        'form': form
    })
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def erea_create(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        if item_id:
            item = get_object_or_404(Erea, pk=item_id)
            form = EreaForm(request.POST, instance=item)
        else:
            form = EreaForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def erea_delete(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        item = get_object_or_404(Erea, pk=pk)
        item.delete()
        return JsonResponse({'success': True})
    return JsonRespons
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)

def gata_list(request):
    items = Gata.objects.all().order_by('-id')
    form = GataForm()
    return render(request, 'masha/add_to_data_base_gata.html', {
        'items': items,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def gata_create(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        if item_id:
            item = get_object_or_404(Gata, pk=item_id)
            form = GataForm(request.POST, instance=item)
        else:
            form = GataForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def gata_delete(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        item = get_object_or_404(Gata, pk=pk)
        item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eng_list(request):
    items = Eng.objects.all().order_by('-id')
    form = EngForm()
    return render(request, 'masha/add_to_data_base_eng.html', {
        'items': items,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eng_create(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        if item_id:
            item = get_object_or_404(Eng, pk=item_id)
            form = EngForm(request.POST, instance=item)
        else:
            form = EngForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eng_delete(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        item = get_object_or_404(Eng, pk=pk)
        item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
# ====== Unit ======

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def unit_list(request):
    items = Unit.objects.all().order_by('-id')
    form = UnitForm()
    return render(request, 'masha/add_to_data_base_unit.html', {
        'items': items,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def unit_create(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        if item_id:
            item = get_object_or_404(Unit, pk=item_id)
            form = UnitForm(request.POST, instance=item)
        else:
            form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
from django.http import JsonResponse
from .models import Form, Mahfth, typ, Type_talb_astshr

@coordinator_or_manager_required
def form_add_masah_nah(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    # جمع البيانات من الـ POST
    data = request.POST
    files = request.FILES

    # الحصول على العناصر المطلوبة من قاعدة البيانات إذا موجودة
    mahfth = Mahfth.objects.get(id=data.get('hid_mah')) if data.get('hid_mah') else None
    typ_a = typ.objects.get(name=data.get('hid_type_document')) if data.get('hid_type_document') else None
    type_talb_astshr = Type_talb_astshr.objects.get(id=data.get('service_list_form_x')) if data.get('service_list_form_x') else None

    # إنشاء النموذج مباشرة
    form_instance = Form.objects.create(
        name=data.get('name_aml'),
        asher=data.get('asher'),
        phone=data.get('phone'),
        card_id=data.get('card_id'),
        img_parsone=files.get('img_parsone'),
        img_document=files.get('img_document'),
        typ=typ_a,
        erea_baser=data.get('erea_11'),
        document_number=data.get('number_dcoum_in_t'),
        typ_aqur=data.get('hid_type_aqure'),
        saft_sahb_talab=data.get('hid_type_form_rakash'),
        ajaml=data.get('text_36'),
        month=data.get('month'),
        year=data.get('year'),
        sent_att=data.get('date_str'),
        streat_name=data.get('streat_name'),
        streat_name_gr=data.get('streat_name_gr'),
        name_wk=data.get('f2'),
        phone_wk=data.get('f4'),
        card_id_wk=data.get('f6'),
        hidden_ansh_hdm=data.get('hid_ansh_hdm'),
        type_talb_astshr=type_talb_astshr,
        mahfth=mahfth
    )

    return JsonResponse({'status': 'success', 'form_id': form_instance.id})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def unit_delete(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        item = get_object_or_404(Unit, pk=pk)
        item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})



# ------------------------ #
#   صفحة أنواع البلوك     #
# ------------------------ #
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Type_block
import re
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_blocks(request):
    blocks = Type_block.objects.all()

    if request.method == 'POST':
        block_id = request.POST.get('id')
        delete_flag = request.POST.get('delete')

        # حذف
        if delete_flag:
            obj = get_object_or_404(Type_block, id=block_id)
            obj.delete()
            return JsonResponse({'success': True})

        # التحقق من الاسم
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'الاسم لا يمكن أن يكون فارغًا.'})
        if len(name) < 3:
            return JsonResponse({'success': False, 'error': 'الاسم يجب أن يكون على الأقل 3 أحرف.'})
        if re.search(r'\d', name):
            return JsonResponse({'success': False, 'error': 'الاسم لا يمكن أن يحتوي على أرقام.'})

        # إضافة / تعديل
        if block_id:
            obj = get_object_or_404(Type_block, id=block_id)
            obj.name = name
            obj.save()
        else:
            Type_block.objects.create(name=name)

        return JsonResponse({'success': True})

    return render(request, 'masha/manage_blocks.html', {'blocks': blocks})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)

def manage_naturals(request):
    form = TypeNaturalForm()
    naturals = Type_natural.objects.all()

    if request.method == 'POST':
        natural_id = request.POST.get('id')
        # حذف
        if 'delete' in request.POST:
            obj = get_object_or_404(Type_natural, id=natural_id)
            obj.delete()
            return JsonResponse({'success': True})

        # إضافة / تعديل
        if natural_id:
            obj = get_object_or_404(Type_natural, id=natural_id)
            form = TypeNaturalForm(request.POST, instance=obj)
        else:
            form = TypeNaturalForm(request.POST)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})

    # GET request: عرض الصفحة
    return render(request, 'masha/manage_naturals.html', {'naturals': naturals, 'form': form})
# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Type_seol, Type_kah
from .forms import TypeSeolForm, TypeKahForm
import re
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_seol(request):
    form = TypeSeolForm()
    seols = Type_seol.objects.all()

    if request.method == 'POST':
        seol_id = request.POST.get('id')
        delete_flag = request.POST.get('delete')

        if delete_flag:
            obj = get_object_or_404(Type_seol, id=seol_id)
            obj.delete()
            return JsonResponse({'success': True})

        name = request.POST.get('name', '').strip()
        if not name or len(name) < 3 or re.search(r'\d', name):
            return JsonResponse({'success': False, 'error': 'الاسم يجب أن يكون على الأقل 3 أحرف وبدون أرقام.'})

        if seol_id:
            obj = get_object_or_404(Type_seol, id=seol_id)
            obj.name = name
            obj.save()
        else:
            Type_seol.objects.create(name=name)

        return JsonResponse({'success': True})

    return render(request, 'masha/seol_nah.html', {'seols': seols, 'form': form})
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)

def manage_kah(request):
    form = TypeKahForm()
    kahs = Type_kah.objects.all()

    if request.method == 'POST':
        kah_id = request.POST.get('id')
        delete_flag = request.POST.get('delete')

        if delete_flag:
            obj = get_object_or_404(Type_kah, id=kah_id)
            obj.delete()
            return JsonResponse({'success': True})

        name = request.POST.get('name', '').strip()
        if not name or len(name) < 3 or re.search(r'\d', name):
            return JsonResponse({'success': False, 'error': 'الاسم يجب أن يكون على الأقل 3 أحرف وبدون أرقام.'})

        if kah_id:
            obj = get_object_or_404(Type_kah, id=kah_id)
            obj.name = name
            obj.save()
        else:
            Type_kah.objects.create(name=name)

        return JsonResponse({'success': True})

    return render(request, 'masha/manage_kah.html', {'kahs': kahs, 'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_typ(request):
    items = typ.objects.all()

    if request.method == 'POST':
        item_id = request.POST.get('id')
        delete_flag = request.POST.get('delete')

        if delete_flag:
            obj = get_object_or_404(typ, number=item_id)
            obj.delete()
            return JsonResponse({'success': True})

        form = TypForm(request.POST)
        if form.is_valid():
            if item_id:  # تعديل
                obj = get_object_or_404(typ, number=item_id)
                obj.number = form.cleaned_data['number']
                obj.save()
            else:  # إضافة
                form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return render(request, 'masha/manage_typ.html', {'items': items, 'form': TypForm()})
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)

def manage_talb_astshr(request):
    items = Type_talb_astshr.objects.all()

    if request.method == 'POST':
        item_id = request.POST.get('id')
        delete_flag = request.POST.get('delete')

        if delete_flag:
            obj = get_object_or_404(Type_talb_astshr, id=item_id)
            obj.delete()
            return JsonResponse({'success': True})

        form = TypeTalbAstshrForm(request.POST)
        if form.is_valid():
            if item_id:
                obj = get_object_or_404(Type_talb_astshr, id=item_id)
                obj.name = form.cleaned_data['name']
                obj.save()
            else:
                form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return render(request, 'masha/manage_talb_astshr.html', {'items': items, 'form': TypeTalbAstshrForm()})
# views.py
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def type_map_list_create(request):
    if request.method == 'POST':
        form = TypeMapForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('masha:type_map_list')  # إعادة التوجيه بعد الإضافة
    else:
        form = TypeMapForm()
    
    # عرض جميع العناصر
    type_maps = Type_map.objects.all()
    return render(request, 'masha/type_map_list.html', {'form': form, 'type_maps': type_maps})



def type_map_ajax(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            pk = request.POST.get('id')
            type_map = get_object_or_404(Type_map, pk=pk)
            type_map.delete()
            return JsonResponse({'status': 'deleted'})

        pk = request.POST.get('id')
        if pk:  # تعديل
            type_map = get_object_or_404(Type_map, pk=pk)
            form = TypeMapForm(request.POST, instance=type_map)
        else:  # إضافة
            form = TypeMapForm(request.POST)

        if form.is_valid():
            obj = form.save()
            return JsonResponse({'status': 'success', 'id': obj.id, 'name': obj.name})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})

    # GET
    type_maps = list(Type_map.objects.values('id', 'name'))
    return JsonResponse({'type_maps': type_maps})
import re
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Eng_nazol
from .forms import EngNazolForm  # تأكد من أن اسم الفورم مطابق في مشروعك
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_eng(request):
    form = EngNazolForm()
    engs = Eng_nazol.objects.select_related('mahfth').all()

    if request.method == 'POST':
        eng_id = request.POST.get('id')
        delete_flag = request.POST.get('delete')

        # حذف
        if delete_flag:
            obj = get_object_or_404(Eng_nazol, id=eng_id)
            obj.delete()
            return JsonResponse({'success': True})

        name = request.POST.get('name', '').strip()
        mahfth_id = request.POST.get('mahfth')

        if not name or len(name) < 3 or re.search(r'\d', name):
            return JsonResponse({'success': False, 'error': 'الاسم يجب أن يكون على الأقل 3 أحرف وبدون أرقام.'})

        if eng_id:
            obj = get_object_or_404(Eng_nazol, id=eng_id)
            obj.name = name
            obj.mahfth_id = mahfth_id
            obj.save()
        else:
            Eng_nazol.objects.create(name=name, mahfth_id=mahfth_id)

        return JsonResponse({'success': True})

    return render(request, 'masha/eng_nazol_page.html', {'form': form, 'engs': engs})

def live_search_ajax_report_masha_print(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(form__name__icontains=query)

        if query.isdigit():
            filters |= Q(id=query)

        matches = report_masahi.objects.select_related(
            "form",
           
            "type_map"
        ).filter(
            filters,
           
           return_masah_jm=True, print_nah=False,
            rafth_adarah_generl=False,
            masahi_convert=False
        )[:50]
        matches = filter_reports(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.form.name if obj.form else '',
                "typ_name": obj.type_map.name if obj.type_map else '',
               "unit_name": obj.form.unit.name if obj.form and hasattr(obj.form, 'unit') else '',
               "gata_name": obj.form.gata.name if obj.form and hasattr(obj.form, 'gata') else '',
                "mahfth_name": obj.resone.name if obj.resone else '',
                "img_document": '',
                "kml_file": obj.kml_file.url if obj.kml_file else '',  # 
            })

    return JsonResponse({"results": results})
    return JsonResponse(results, safe=False)
def live_search_ajax_report_masha_print_archif(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(form__name__icontains=query)

        if query.isdigit():
            filters |= Q(id=query)

        matches = report_masahi.objects.select_related(
            "form",
            "type_map"
           
         
        ).filter(
          filters,
            return_masah_jm=True,
            rafth_adarah_generl=False,
            masahi_convert=False,
            rafth_adarah_generl_by_manager_mahfth=False

          
         

        )[:50]
        matches = filter_reports(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.form.name if obj.form else '',
                "typ_name": obj.type_map.name if obj.type_map else '',
               "unit_name": obj.form.unit.name if obj.form and hasattr(obj.form, 'unit') else '',
               "mahfth_name": obj.form.mahfth.name if obj.form and hasattr(obj.form, 'mahfth') else '',
               
                "img_document": '',
                
            })

    return JsonResponse({"results": results})
    return JsonResponse(results, safe=False)
@user_passes_test(lambda u: u.is_superuser or u.has_perm('masha.add_unit'))
def print_report(request):
    print_report_x= report_masahi.objects.filter( return_masah_jm=True, print_nah=False )
    context={'print_report_x':print_report_x}
    return render(request,'masha/print_report.html',context)
@coordinator_or_manager_required
@mahfth_screen_required
def interface_nah_astshr(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=False,hidden_ansh_hdm="استشارة" ), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return render(request,'masha/interface_nah.html',context)
def show_tsrah_exit_eng_by_manger_astsherh(request):
    form=Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=False,hidden_ansh_hdm="استشارة").order_by('-id')
    context={"form":form}
    return render(request,'masha/show_tsrah_exit_eng_by_manger_ashchr.html',context)
def print_talbt_nah(request):
        form=Form.objects.filter(hidden_ansh_hdm="استشارة").order_by('-id')
        context={"form":form}
        return render(request,'masha/print_talbt_nah.html',context)
def print_talbt_nah_bana(request):

        form=Form.objects.filter(hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
        context={"form":form}
        return render(request,'masha/print_talbt_nah.html',context)
    

def rafth_mamlah_form_by_manger(request):
    form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,tslem_rafth=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
    context={'form':form}
    return render(request,'masha/reasone_rafth.html',context)
def rafth_mamlah_form_by_manger_astsherh(request):
    form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,tslem_rafth=False,hidden_ansh_hdm="استشارة").order_by('-id')
    context={'form':form}
    return render(request,'masha/reason_rafth_astshr.html',context)

def rafth_mamlah_form_by_manger_report(request):
    form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
    context={'form':form}
    return render(request,'masha/reasone_rafth_report.html',context)

def live_search_rafth_mamlah_bana(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) | Q(id__icontains=query)

        matches = Form.objects.filter(
            filters,
            rafth_maml=True,
            hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "streat_name": obj.streat_name,
               
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
               
            })

    return JsonResponse({"results": results})

def rafth_mamlah_form_by_manger_report_astsherh(request):
    form = Form.objects.filter(
        show_tasrah_karoj=False,
        rafth_maml=True,
        talb_astkml=False,
        hidden_ansh_hdm="استشارة"
    ).order_by('-id')

    context = {'form': form}
    return render(request, 'masha/reson_refth_astsharah_report.html', context)


def live_search_rafth_mamlah(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) | Q(name_wk__icontains=query) | Q(streat_name__icontains=query)
        if query.isdigit():
            filters |= Q(id=query)

        matches = Form.objects.filter(
            filters,
            show_tasrah_karoj=False,
            rafth_maml=True,
            talb_astkml=False,
            hidden_ansh_hdm="استشارة"
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "streat_name": obj.streat_name,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "rasone_rafth_maml": obj.rasone_rafth_maml,
                "gata_name": getattr(getattr(obj.unit, 'gata', None), 'name', ''),
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
            })

    return JsonResponse({"results": results})
def talb_astkmal_mamlah(request):
    form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,tslem_astkmal=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
    context={'form':form}
    return render(request,'masha/talb_astkmal_doc.html',context)
def talb_astkmal_mamlah_astsherh(request):
      form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,tslem_astkmal=False,hidden_ansh_hdm="استشارة").order_by('-id')
      context={'form':form}
      return render(request,'masha/talb_astkmal_doc_asthshrah.html',context)

def talb_astkmal_mamlah_report(request):
    form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص").order_by('-id')
    context={'form':form}
    return render(request,'masha/talb_astkmal_report_bana_nah.html',context)
def talb_astkmal_mamlah_report_astsherh(request):
    form=Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,hidden_ansh_hdm="استشارة").order_by('-id')
    context={'form':form}
    return render(request,'masha/talb_astkmal_doc_report.html',context)
from django.http import JsonResponse
from django.db.models import Q
from .models import Form
def live_search_talb_astkmal_bana(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) 

        matches = Form.objects.filter(
            filters,
            show_tasrah_karoj=True,
            hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "streat_name": obj.streat_name,
                "name_documnt": obj.name_documnt,
               
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
               
            })

    return JsonResponse({"results": results})
def live_search_ajax_tsrah_exit_nah(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) 

        matches = Form.objects.filter(
            filters,
           show_tasrah_karoj=False,rafth_maml=False,talb_astkml=False, return_form=False, digital=False
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name": obj.name,
                "name_wk": obj.name_wk,
                "streat_name": obj.streat_name,
                "name_documnt": obj.name_documnt,
               
                
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
               
            })

    return JsonResponse({"results": results})
def live_search_talb_astkmal(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        filters = Q(name__icontains=query) | Q(name_wk__icontains=query) | Q(streat_name__icontains=query)
        if query.isdigit():
            filters |= Q(id=query)

        matches = Form.objects.filter(
            filters,
            show_tasrah_karoj=False,
            rafth_maml=False,
            talb_astkml=True,
            hidden_ansh_hdm="استشارة"
        ).order_by('-id')[:50]
        matches = filter_forms(matches, request.user)

        for obj in matches:
            results.append({
                "id": obj.id,
                "name_documnt": obj.name_documnt if hasattr(obj, 'name_documnt') else '',
                "streat_name": obj.streat_name if hasattr(obj, 'streat_name') else '',
                "name": obj.name if hasattr(obj, 'name') else '',
                "name_wk": obj.name_wk if hasattr(obj, 'name_wk') else '',
                "unit_name": obj.unit.name if obj.unit else '',
                "gata_name": obj.unit.gata.name if obj.unit and hasattr(obj.unit, 'gata') and obj.unit.gata else '',
                "mahfth_name": obj.mahfth.name if obj.mahfth else '',
                "hidden_ansh_hdm": obj.hidden_ansh_hdm,
                "ajaml": obj.ajaml,
            })

    return JsonResponse({"results": results})

def  interface_nah_astshr_json(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,tslem_rafth=False,
hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,tslem_astkmal=False,
hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=False,
hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return JsonResponse({
        "num_unread": num_unread,
        "num_unread_2": num_unread_2,
        "num_unread_3": num_unread_3,
       
    })
def interface_nah_astshr_json_astsherh(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,tslem_rafth=False,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,tslem_astkmal=False,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False,tr_masah=False,exit_eng=False,hidden_ansh_hdm="استشارة"), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return JsonResponse({
        "num_unread": num_unread,
        "num_unread_2": num_unread_2,
        "num_unread_3": num_unread_3,
       
    })


def report_state_talbat_nah(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"
), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"
), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"
), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return render(request,'masha/report_state_talbat_nah.html',context)
def report_state_talbat_nah_astshr(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,hidden_ansh_hdm="استشارة"), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return render(request,'masha/report_state_talbat_nah_asthsr.html',context)

def report_state_talbat_nah_json(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,
hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,
hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,
hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return JsonResponse({
        "num_unread": num_unread,
        "num_unread_2": num_unread_2,
        "num_unread_3": num_unread_3,
       
    })
def report_state_talbat_nah_json_astsherh(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,hidden_ansh_hdm="استشارة"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,hidden_ansh_hdm="استشارة"), request.user).count() 
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,'num_unread_2':num_unread_2}
    return JsonResponse({
        "num_unread": num_unread,
        "num_unread_2": num_unread_2,
        "num_unread_3": num_unread_3,
       
    })


@coordinator_or_manager_required
@mahfth_screen_required
def enter_data_report_masahi_screen(request):
    num_unread=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=True,talb_astkml=False,tslem_rafth=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count()
    num_unread_3 = filter_forms(Form.objects.filter(show_tasrah_karoj=True,return_form=False,digital=False, tr_masah=False,exit_eng=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count() 
    num_unread_2=filter_forms(Form.objects.filter(show_tasrah_karoj=False,rafth_maml=False,talb_astkml=True,tslem_rafth=False,hidden_ansh_hdm="اصدار تقرير مساحي بغرض الترخيص"), request.user).count()
    context={'num_unread':num_unread,'num_unread_3':num_unread_3,"num_unread_2":num_unread_2}
    return render(request,'masha/enter_data_report_masahi_screen.html',context)
    