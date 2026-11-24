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


def get_user_mahfth(user):
    """إرجاع كائن المديرية الخاص بالمستخدم أو None.

    الأولوية:
        1) Profile.mahfth  (الحقل الجديد)
        2) Profile.city.mahfth  (الحقل القديم للتوافق مع البيانات السابقة)
    """
    if user is None or not user.is_authenticated:
        return None

    if user.is_superuser or user.is_staff:
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


def filter_queryset_by_mahfth(queryset, user, field="mahfth"):
    """تقييد الـ queryset بمديرية المستخدم (إن كان مستخدماً عادياً).

    يقبل field مساراً واحداً أو عدة مسارات بديلة، ويدعم الـ queryset
    المقطّع بإعادة تطبيق الحد بعد فلترة المديرية.
    """
    if user is None or not user.is_authenticated:
        return queryset.none()
    if user.is_superuser or user.is_staff:
        return queryset

    mahfth = get_user_mahfth(user)
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
    if user.is_superuser or user.is_staff:
        return Mahfth.objects.all()

    mahfth = get_user_mahfth(user)
    if mahfth is None:
        return Mahfth.objects.none()
    return Mahfth.objects.filter(id=mahfth.id)


def resolve_mahfth_for_user(user, mahfth_id):
    """تحديد المديرية المسموح بها عند إنشاء/تعديل البيانات.

    * المدير (staff/superuser): يستطيع اختيار أي مديرية.
    * المستخدم العادي: يُجبَر على مديريته دائماً مهما أرسل من بيانات.

    يرجع (mahfth, error_message).
    """
    from .models import Mahfth

    if user is None or not user.is_authenticated:
        return None, "يجب تسجيل الدخول أولاً."

    if user.is_superuser or user.is_staff:
        if not mahfth_id:
            return None, "يجب تحديد المديرية."
        try:
            return Mahfth.objects.get(id=mahfth_id), None
        except (Mahfth.DoesNotExist, ValueError, TypeError):
            return None, "المديرية المحددة غير موجودة."

    my_mahfth = get_user_mahfth(user)
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
