from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Permission
from django import forms
from django.contrib.auth.forms import AuthenticationForm


 # حقل CAPTCHA
class UserPermissionForm(forms.Form):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="اختر الصلاحيات"
    )


class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')

class SignupForm(UserCreationForm):
    username = forms.CharField(label='ادخل اسم المستخدم', required=True)
    email = forms.EmailField(label='ادخل الايميل', required=True)
  
    password1 = forms.CharField(
        label='ادخل كلمة المرور الجديدة',
        widget=forms.PasswordInput,
        required=True
    )
    password2 = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput,
        required=True


    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserForm(forms.ModelForm):
	class Meta:
		  model=User
		  fields=['username','first_name','last_name','email']
class ProfileForm(forms.ModelForm):
	class Meta:
		  model=Profile
		  fields=['city','phone_number']