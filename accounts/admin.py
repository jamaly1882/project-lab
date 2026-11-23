from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import City, Profile

admin.site.register(City)


class ProfileInline(admin.StackedInline):
    """تحديد المديرية مباشرة من صفحة المستخدم في لوحة الإدارة."""

    model = Profile
    can_delete = False
    verbose_name = "ملف المستخدم"
    verbose_name_plural = "ملف المستخدم (المديرية والهاتف)"
    fields = ("mahfth", "phone_number", "city")
    extra = 0


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    list_display = ("user", "mahfth", "phone_number", "city")
    list_filter = ("mahfth",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "mahfth__name")


# إعادة تسجيل نموذج المستخدم مع إظهار المديرية
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "get_full_name",
        "get_mahfth",
        "is_active",
        "is_staff",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "profile__mahfth")
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "profile__mahfth__name",
    )

    @admin.display(description="المديرية")
    def get_mahfth(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.mahfth.name if profile and profile.mahfth else "—"

    @admin.display(description="الاسم الكامل")
    def get_full_name(self, obj):
        return obj.get_full_name() or "—"
