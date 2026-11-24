"""لوحة إدارة المستخدمين (إنشاء / تعديل / تعطيل / حذف) من لوحة التحكم.

كل مستخدم يُربط بمديرية من جدول mahfth، وعند تسجيل دخوله تظهر مديريته فقط.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Profile
from accounts.user_forms import UserCreateForm, UserUpdateForm


def is_admin_user(user):
    """المسؤول عن إدارة المستخدمين: مدير النظام أو أي حساب staff."""
    return bool(user.is_authenticated and (user.is_superuser or user.is_staff))


admin_required = user_passes_test(
    is_admin_user,
    login_url="accounts:login",
)


def _search_users(query):
    users = User.objects.select_related("profile__mahfth").order_by("-date_joined")
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(profile__mahfth__name__icontains=query)
            | Q(profile__role__icontains=query)
        )
    return users


@login_required
@admin_required
def user_manage(request):
    """عرض قائمة المستخدمين + نموذج إضافة مستخدم جديد."""
    query = (request.GET.get("q") or "").strip()

    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = getattr(user, "profile", None)
            assignment = (
                f"وربطه بـ {profile.mahfth.name}"
                if profile and profile.mahfth
                else "دون ربطه بمديرية"
            )
            messages.success(
                request,
                f"تم إنشاء المستخدم «{user.username}» بنجاح، {assignment}.",
            )
            return redirect("accounts:user_manage")
        messages.error(request, "تعذّر إنشاء المستخدم، يرجى تصحيح الأخطاء أدناه.")
    else:
        form = UserCreateForm()

    context = {
        "form": form,
        "users": _search_users(query),
        "query": query,
        "users_count": User.objects.count(),
        "active_count": User.objects.filter(is_active=True).count(),
        "mahfth_users_count": Profile.objects.filter(mahfth__isnull=False).count(),
    }
    return render(request, "accounts/user_manage.html", context)


@login_required
@admin_required
def user_edit(request, pk):
    """تعديل بيانات مستخدم: الاسم المديرية وكلمة المرور."""
    user_obj = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f"تم تحديث بيانات المستخدم «{user.username}» بنجاح."
            )
            return redirect("accounts:user_manage")
        messages.error(request, "تعذّر حفظ التعديلات، يرجى تصحيح الأخطاء أدناه.")
    else:
        form = UserUpdateForm(instance=user_obj)

    profile = getattr(user_obj, "profile", None)
    context = {
        "form": form,
        "user_obj": user_obj,
        "profile": profile,
    }
    return render(request, "accounts/user_edit.html", context)


@login_required
@admin_required
@require_POST
def user_toggle_active(request, pk):
    """تعطيل / تفعيل حساب مستخدم."""
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj == request.user:
        return JsonResponse(
            {"success": False, "error": "لا يمكنك تعطيل حسابك الحالي."}, status=400
        )

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=["is_active"])
    return JsonResponse(
        {
            "success": True,
            "is_active": user_obj.is_active,
            "message": "تم تفعيل الحساب." if user_obj.is_active else "تم تعطيل الحساب.",
        }
    )


@login_required
@admin_required
@require_POST
def user_delete(request, pk):
    """حذف مستخدم."""
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj == request.user:
        return JsonResponse(
            {"success": False, "error": "لا يمكنك حذف حسابك الحالي."}, status=400
        )

    if user_obj.is_superuser and (
        User.objects.filter(is_superuser=True, is_active=True).count() <= 1
    ):
        return JsonResponse(
            {"success": False, "error": "لا يمكن حذف آخر مدير للنظام."}, status=400
        )

    username = user_obj.username
    user_obj.delete()
    return JsonResponse(
        {"success": True, "message": f"تم حذف المستخدم «{username}»."}
    )
