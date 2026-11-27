"""
أدوات مساعدة لربط المستخدم بالمديرية (جدول Mahfth) وتقييد البيانات المعروضة.

القاعدة:
    * مدير النظام (superuser / staff) يرى جميع المديريات.
    * المستخدم العادي يرى مديريته فقط (المحددة في ملفه الشخصي Profile.mahfth).
"""

from django.db.models import Q

from .models import Form, report_masahi

# أسماء الحقول في نموذج report_masahi التي تشير إلى المديرية
REPORT_MAHFTH_FIELDS = ("mahfth", "form__mahfth")

# أدوار قسم/إدارة المساحة (نفس القيم الموجودة في accounts.Profile.ROLE_CHOICES)
ROLE_DEPARTMENT_HEAD = "رئيس قسم مساحة"
ROLE_SURVEY_ENGINEER = "مهندس مساحة"
ROLE_DEPARTMENT_COORDINATOR = "منسق قسم مساحة"
ROLE_AREA_MANAGER = "مدير إدارة المساحة"

# الصفحة الرئيسية (البروفايل) الخاصة بكل دور بعد تسجيل الدخول
ROLE_HOME_URL_NAMES = {
    ROLE_DEPARTMENT_HEAD: "masha:show_manager_masah_nah",
    ROLE_SURVEY_ENGINEER: "masha:show_astmrat",
    ROLE_DEPARTMENT_COORDINATOR: "masha:interface",
    ROLE_AREA_MANAGER: "masha:screen_adrat_ver",
}


def get_user_role(user):
    """دور المستخدم من ملفه الشخصي (نص فارغ عند عدم وجود دور)."""
    if user is None or not getattr(user, "is_authenticated", False):
        return ""
    profile = getattr(user, "profile", None)
    if profile is None:
        return ""
    return (getattr(profile, "role", "") or "").strip()


def role_home_url_name(user):
    """اسم رابط الصفحة الرئيسية الخاصة بدور المستخدم أو None."""
    return ROLE_HOME_URL_NAMES.get(get_user_role(user))


def is_area_manager(user):
    """مدير إدارة المساحة: مسؤول عن الإدارة كلها ولا يرتبط بمديرية واحدة."""
    return get_user_role(user) == ROLE_AREA_MANAGER


def get_user_mahfth(user):
    """إرجاع كائن المديرية الخاص بالمستخدم أو None.

    الأولوية:
        1) Profile.mahfth  (الحقل الجديد)
        2) Profile.city.mahfth  (الحقل القديم للتوافق مع البيانات السابقة)
    """
    if user is None or not user.is_authenticated:
        return None

    if user.is_superuser:
        return None

    profile = getattr(user, "profile", None)
    if profile is None:
        return None

    if profile.mahfth_id:
        return profile.mahfth

    city = getattr(profile, "city", None)
    if city is not None and city.mahfth_id:
        return city.mahfth

    return None


def is_global_mahfth_manager(user):
    """True only for global admins, not staff accounts assigned to a district."""
    if user is None or not user.is_authenticated:
        return False
    if is_area_manager(user):
        return True
    return user.is_superuser or (user.is_staff and get_user_mahfth(user) is None)


def filter_queryset_by_mahfth(queryset, user, field="mahfth"):
    """تقييد الـ queryset بمديرية المستخدم المرتبط بها، بما في ذلك الموظف المعيّن.

    يقبل field مساراً واحداً أو عدة مسارات بديلة، ويدعم الـ queryset
    المقطّع بإعادة تطبيق الحد بعد فلترة المديرية.
    """
    if user is None or not user.is_authenticated:
        return queryset.none()
    if user.is_superuser or is_area_manager(user):
        # مدير إدارة المساحة يرى معاملات جميع المديريات.
        return queryset

    mahfth = get_user_mahfth(user)
    # A staff account explicitly tied to a district (for example, a department
    # head) is district-scoped too. Unassigned staff remain global administrators.
    if user.is_staff and mahfth is None:
        return queryset
    if mahfth is None:
        return queryset.none()

    fields = (field,) if isinstance(field, str) else tuple(field)
    scope_filter = Q(**{fields[0]: mahfth})
    # Treat later paths as legacy fallbacks only when the primary relation is empty.
    # This prevents an inconsistent secondary relation from overriding a direct
    # assignment to a different district.
    for path in fields[1:]:
        scope_filter |= Q(**{f"{fields[0]}__isnull": True, path: mahfth})

    if queryset.query.is_sliced:
        low = queryset.query.low_mark
        high = queryset.query.high_mark
        base = queryset.all()
        base.query.clear_limits()
        return base.filter(scope_filter)[low:high]

    return queryset.filter(scope_filter)


def filter_forms(queryset, user):
    """تقييد النماذج بمديرية المستخدم، حتى للبيانات القديمة ذات الربط غير المباشر."""
    return filter_queryset_by_mahfth(
        queryset,
        user,
        field=("mahfth", "unit__mahfth"),
    )


def filter_reports(queryset, user):
    """تقييد التقارير بمديرية النموذج أو الوحدة/القطاع المرتبط به."""
    return filter_queryset_by_mahfth(
        queryset,
        user,
        field=(
            "form__mahfth",
            "form__unit__mahfth",
        ),
    )


def visible_mahfth_list(user):
    """قائمة المديريات التي يحق للمستخدم رؤيتها (للقوائم المنسدلة)."""
    from .models import Mahfth

    if user is None or not user.is_authenticated:
        return Mahfth.objects.none()
    if user.is_superuser or is_area_manager(user):
        return Mahfth.objects.all()

    mahfth = get_user_mahfth(user)
    if user.is_staff and mahfth is None:
        return Mahfth.objects.all()
    if mahfth is None:
        return Mahfth.objects.none()
    return Mahfth.objects.filter(id=mahfth.id)


def resolve_mahfth_for_user(user, mahfth_id):
    """تحديد المديرية المسموح بها عند إنشاء/تعديل البيانات.

    * المشرف العام أو الموظف غير المرتبط بمديرية: يستطيع اختيار أي مديرية.
    * المستخدم المرتبط بمديرية، بما فيه رئيس القسم: يُجبَر على مديريته.

    يرجع (mahfth, error_message).
    """
    from .models import Mahfth

    if user is None or not user.is_authenticated:
        return None, "يجب تسجيل الدخول أولاً."

    my_mahfth = get_user_mahfth(user)

    # Superusers, and staff accounts without a district assignment, are global
    # administrators. Staff accounts assigned to a district follow the same
    # district boundary as other users.
    if is_area_manager(user) or user.is_superuser or (user.is_staff and my_mahfth is None):
        if not mahfth_id:
            return None, "يجب تحديد المديرية."
        try:
            return Mahfth.objects.get(id=mahfth_id), None
        except (Mahfth.DoesNotExist, ValueError, TypeError):
            return None, "المديرية المحددة غير موجودة."

    if my_mahfth is None:
        return None, "لم يتم ربط حسابك بأي مديرية، راجع مدير النظام."

    return my_mahfth, None


def get_user_city(user):
    """إرجاع «مدينة» المستخدم من ملفه الشخصي (إن وجدت)."""
    if user is None or not user.is_authenticated:
        return None

    profile = getattr(user, "profile", None)
    if profile is None:
        return None

    return getattr(profile, "city", None)


def get_user_city_name(user):
    """اسم مدينة المستخدم.

    الأولوية:
        1) Profile.city.city  (المدينة المسجّلة في الملف الشخصي)
        2) اسم مديرية المستخدم  (Profile.mahfth أو Profile.city.mahfth)
    """
    city = get_user_city(user)
    if city is not None:
        name = (city.city or "").strip()
        if name:
            return name

    mahfth = get_user_mahfth(user)
    if mahfth is not None:
        return (mahfth.name or "").strip()

    return ""


def scope_name_for_user(user):
    """الاسم المستخدم لمطابقة «مدينة» المستخدم مع المديريات/الروابط.

    يجمع بين المدينة والمديرية حتى تعمل المقارنة في القوالب سواء رُبط
    المستخدم بمدينة أو بمديرية مباشرة.
    """
    return get_user_city_name(user)
