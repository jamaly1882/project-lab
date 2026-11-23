"""متغيرات مشتركة في كل القوالب: مديرية المستخدم الحالي."""


def user_mahfth(request):
    """يعرض مديرية المستخدم في القوالب باسم user_mahfth / my_mahfth_name."""
    user = getattr(request, "user", None)

    if user is None or not user.is_authenticated:
        return {"user_mahfth": None, "my_mahfth_name": ""}

    from masha.scoping import get_user_mahfth

    mahfth = get_user_mahfth(user)
    return {
        "user_mahfth": mahfth,
        "my_mahfth_name": mahfth.name if mahfth else "",
    }
