"""نماذج إدارة المستخدمين من لوحة التحكم."""

from django import forms
from django.contrib.auth.models import User

from accounts.models import Profile


class RedirectAfterSaveMixin:
    """إعادة توجيه المستخدم إلى الصفحة نفسها بعد الحفظ الناجح."""

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.redirect_name = kwargs.pop("redirect_name", "masha:user_manage")
        super().__init__(*args, **kwargs)

    def _redirect(self):
        from django.shortcuts import redirect

        if self.request is not None:
            return redirect(self.redirect_name)
        return None


class _BaseUserForm(RedirectAfterSaveMixin, forms.ModelForm):
    mahfth = forms.ModelChoiceField(
        label="المديرية",
        queryset=None,           # يُحدد في __init__
        required=False,          # يُتحقق من إلزاميته بحسب الدور في clean().
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="--- اختر المديرية ---",
    )
    role = forms.ChoiceField(
        label="الدور",
        choices=(("", "--- اختر الدور ---"),) + Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    phone_number = forms.CharField(
        label="رقم الهاتف (اختياري)",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ادخل رقم الهاتف"}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "username": "اسم المستخدم (بالإنجليزية)",
            "first_name": "الاسم الأول",
            "last_name": "الاسم الأخير",
            "email": "البريد الإلكتروني",
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ادخل اسم المستخدم بالانجليزي",
                    "dir": "ltr",
                }
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ادخل الاسم الأول"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ادخل الاسم الأخير"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ادخل البريد الإلكتروني",
                    "dir": "ltr",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        from masha.models import Mahfth

        super().__init__(*args, **kwargs)
        self.fields["mahfth"].queryset = Mahfth.objects.all().order_by("name")

        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
            except Exception:
                profile = None
            if profile is not None:
                self.fields["mahfth"].initial = profile.mahfth_id
                self.fields["role"].initial = profile.role
                self.fields["phone_number"].initial = profile.phone_number

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        if role != "مدير إدارة المساحة" and not cleaned.get("mahfth"):
            self.add_error("mahfth", "اختيار المديرية مطلوب لهذا الدور.")
        return cleaned

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise forms.ValidationError("اسم المستخدم مطلوب.")
        qs = User.objects.filter(username__iexact=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("اسم المستخدم موجود مسبقاً، اختر اسماً آخر.")
        return username

    def save(self, commit=True):
        user = super().save(commit=commit)
        if not commit:
            return user

        profile, _ = Profile.objects.get_or_create(
            user=user, defaults={"phone_number": ""}
        )
        profile.role = self.cleaned_data.get("role") or ""
        profile.mahfth = (
            None
            if profile.role == "مدير إدارة المساحة"
            else self.cleaned_data.get("mahfth")
        )
        profile.city = None  # المدينة لم تعد تُختار من نموذج إدارة المستخدمين.
        phone = (self.cleaned_data.get("phone_number") or "").strip()
        if phone or not profile.phone_number:
            profile.phone_number = phone
        profile.save()
        return user


class UserCreateForm(_BaseUserForm):
    """إضافة مستخدم جديد: الاسم + كلمة المرور + المديرية."""

    password1 = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "ادخل كلمة المرور", "dir": "ltr"}
        ),
    )
    password2 = forms.CharField(
        label="تأكيد كلمة المرور",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "أعد إدخال كلمة المرور",
                "dir": "ltr",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "كلمتا المرور غير متطابقتين.")
        if p1 and len(p1) < 6:
            self.add_error("password1", "كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
            # حفظ الملف الشخصي (المديرية + الهاتف)
            super().save(commit=True)
        return user


class UserUpdateForm(_BaseUserForm):
    """تعديل بيانات مستخدم: الاسم + المديرية (+ تعيين كلمة مرور جديدة اختيارياً)."""

    new_password1 = forms.CharField(
        label="كلمة مرور جديدة (اتركها فارغة إذا لا تريد التغيير)",
        required=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "كلمة مرور جديدة", "dir": "ltr"}
        ),
    )
    new_password2 = forms.CharField(
        label="تأكيد كلمة المرور الجديدة",
        required=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "تأكيد كلمة المرور", "dir": "ltr"}
        ),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 or p2:
            if p1 != p2:
                self.add_error("new_password2", "كلمتا المرور غير متطابقتين.")
            elif p1 and len(p1) < 6:
                self.add_error("new_password1", "كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("new_password1")
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
            self.save_m2m()
            super().save(commit=True)
        return user
