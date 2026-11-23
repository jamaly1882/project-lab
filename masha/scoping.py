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

    يدعم أيضاً الـ queryset الذي تم تقطيعه ([:50]) بإزالة الحدود ثم
    إعادة تطبيقها بعد الفلترة.
    """
    if user is None or not user.is_authenticated:
        return queryset.none()
    if user.is_superuser or user.is_staff:
        return queryset

    mahfth = get_user_mahfth(user)
    if mahfth is None:
        # مستخدم عادي بدون مديرية = لا يرى أي بيانات
        return queryset.none()

    if queryset.query.is_sliced:
        low = queryset.query.low_mark
        high = queryset.query.high_mark
        base = queryset.all()
        base.query.clear_limits()
        filtered = base.filter(**{field: mahfth})
        return filtered[low:high]

    return queryset.filter(**{field: mahfth})


def filter_forms(queryset, user):
    """تقييد نماذج Form بمديرية المستخدم."""
    return filter_queryset_by_mahfth(queryset, user, field="mahfth")


def filter_reports(queryset, user):
    """تقييد تقارير report_masahi بمديرية المستخدم."""
    return filter_queryset_by_mahfth(queryset, user, field="form__mahfth")


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
