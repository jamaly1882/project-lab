"""متغيرات مشتركة في كل القوالب: مديرية/مدينة المستخدم الحالي."""


def _display_full_name(user):
    """الاسم الكامل الظاهر في الواجهة، مع بديل مناسب."""
    full_name = ""
    try:
        full_name = (user.get_full_name() or "").strip()
    except Exception:
        full_name = ""
    return full_name or (getattr(user, "username", "") or "").strip() or "مستخدم"


def _initials(name):
    """أول حرف من أول كلمة وأول حرف من آخر كلمة (يصلح للعربية والإنجليزية)."""
    parts = [part for part in (name or "").split() if part]
    if not parts:
        return "م"
    if len(parts) == 1:
        return parts[0][:1]
    return parts[0][:1] + parts[-1][:1]


def _empty_profile_context():
    return {
        "user_mahfth": None,
        "my_mahfth_name": "",
        "user_city": None,
        "my_city_name": "",
        "my_scope_name": "",
        "is_system_manager": False,
        "user_role": "",
        "user_profile": None,
        "my_full_name": "",
        "my_phone_number": "",
        "my_initials": "",
    }


def user_mahfth(request):
    """يعرض مديرية ومدينة المستخدم في كل القوالب.

    المتغيرات المتاحة:
        * user_mahfth    : كائن المديرية (أو None للمدير)
        * my_mahfth_name : اسم المديرية
        * user_city      : كائن المدينة من الملف الشخصي (أو None)
        * my_city_name   : اسم المدينة، وإن لم تُسجَّل يُستخدم اسم المديرية
        * my_scope_name  : الاسم المستخدم لمقارنة الروابط (مدينة/مديرية)
        * is_system_manager : هل المستخدم مدير نظام (يرى كل المديريات)؟
        * user_role      : الدور من الملف الشخصي (رئيس قسم مساحة / مهندس مساحة ...)
        * user_profile   : كائن Profile نفسه (أو None)
        * my_full_name   : الاسم الكامل (أو اسم المستخدم عند غيابه)
        * my_phone_number: رقم الهاتف من الملف الشخصي
        * my_initials    : أحرف الأفاتار (أول حرف من الاسم الأول والأخير)
    """
    user = getattr(request, "user", None)

    if user is None or not user.is_authenticated:
        return _empty_profile_context()

    from masha.scoping import get_user_city, get_user_city_name, get_user_mahfth

    mahfth = get_user_mahfth(user)
    city = get_user_city(user)
    scope_name = get_user_city_name(user)

    try:
        profile = user.profile
    except Exception:
        profile = None

    role = (getattr(profile, "role", "") or "").strip() if profile is not None else ""
    phone = (getattr(profile, "phone_number", "") or "").strip() if profile is not None else ""
    full_name = _display_full_name(user)

    return {
        "user_mahfth": mahfth,
        "my_mahfth_name": mahfth.name if mahfth else "",
        "user_city": city,
        "my_city_name": scope_name,
        "my_scope_name": scope_name,
        "is_system_manager": bool(user.is_superuser or user.is_staff),
        "user_role": role,
        "user_profile": profile,
        "my_full_name": full_name,
        "my_phone_number": phone,
        "my_initials": _initials(full_name),
    }
