"""متغيرات مشتركة في كل القوالب: مديرية/مدينة المستخدم الحالي."""


def user_mahfth(request):
    """يعرض مديرية ومدينة المستخدم في كل القوالب.

    المتغيرات المتاحة:
        * user_mahfth    : كائن المديرية (أو None للمدير)
        * my_mahfth_name : اسم المديرية
        * user_city      : كائن المدينة من الملف الشخصي (أو None)
        * my_city_name   : اسم المدينة، وإن لم تُسجَّل يُستخدم اسم المديرية
        * my_scope_name  : الاسم المستخدم لمقارنة الروابط (مدينة/مديرية)
        * is_system_manager : هل المستخدم مدير نظام (يرى كل المديريات)؟
    """
    user = getattr(request, "user", None)

    if user is None or not user.is_authenticated:
        return {
            "user_mahfth": None,
            "my_mahfth_name": "",
            "user_city": None,
            "my_city_name": "",
            "my_scope_name": "",
            "is_system_manager": False,
            "user_role": "",
        }

    from masha.scoping import get_user_city, get_user_city_name, get_user_mahfth

    mahfth = get_user_mahfth(user)
    city = get_user_city(user)
    scope_name = get_user_city_name(user)

    try:
        role = user.profile.role
    except Exception:
        role = ""

    return {
        "user_mahfth": mahfth,
        "my_mahfth_name": mahfth.name if mahfth else "",
        "user_city": city,
        "my_city_name": scope_name,
        "my_scope_name": scope_name,
        "is_system_manager": bool(user.is_superuser or user.is_staff),
        "user_role": role,
    }
