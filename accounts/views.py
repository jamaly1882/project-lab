from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse
from  .form import SignupForm,UserForm,ProfileForm,LoginForm
from .models import Profile
from django.contrib.auth import authenticate,login
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required,permission_required
from django.core.serializers import serialize 
from django.contrib.auth.models import User
from django.http import  HttpResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.utils.http import url_has_allowed_host_and_scheme
def Signup(request):
		 if request.method=="POST":
		 	form=SignupForm(request.POST)
		 	if form.is_valid():
		 	   form.save()
		 	   username=form.cleaned_data['username']
		 	   password=form.cleaned_data['password1']
		 	   user=authenticate(username=username,password=password)
		 	   login(request,user)
		 	   return redirect('masha:interface')


		 else:
		 	   form=SignupForm()
		 return render(request, 'registration/signup.html',{'form':form})

def profile(request):
	 profile=Profile.objects.get(user=request.user)

	 return render(request,'masha/interface.html',{'profile':profile})


def profile_edite(request):
		profile=Profile.objects.get(user=request.user)
		if request.method=="POST":
		 	userform=UserForm(request.POST,instance=request.user)
		 	profileform=ProfileForm(request.POST,request.FILES,instance=profile)
		 	if  userform.is_valid() and profileform.is_valid():
		 		userform.save()
		 		profileform.user=request.user
		 		profileform.save()

		else:
		 	userform=UserForm(instance=request.user)
		 	profileform=ProfileForm(instance=profile)
		return render(request,'accounts/edite_profile.html',{'userform':userform,'profileform':profileform})


def login_view(request):
    """صفحة تسجيل الدخول الرئيسية للنظام.

    ملاحظة مهمة: هذه الصفحة يجب أن تعرض حقلي «اسم المستخدم» و«كلمة المرور»
    دائماً، حتى لا تظهر بطاقة الدخول فارغة (بدون حقول إدخال).
    """
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if next_url and not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ''

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                return render(
                    request,
                    "registration/login.html",
                    {
                        "form": LoginForm(request),
                        "error": "هذا الحساب معطّل، يرجى مراجعة مدير النظام.",
                        "next": next_url,
                    },
                )

            login(request, user)

            if next_url:
                return redirect(next_url)

            # أصحاب الأدوار المساحية يدخلون مباشرة إلى شاشة قسمهم؛ بقية
            # المستخدمين يستمرون بالذهاب إلى لوحة التحكم.
            try:
                role = user.profile.role
            except Exception:
                role = ""
            if role == "رئيس قسم مساحة":
                return redirect("masha:show_manager_masah_nah")
            if role == "مهندس مساحة":
                return redirect("masha:show_astmrat")
            if role == "منسق قسم مساحة":
                return redirect("masha:interface")
            return redirect('masha:index')

        return render(
            request,
            "registration/login.html",
            {
                "form": LoginForm(request, data=request.POST),
                "error": "اسم المستخدم أو كلمة المرور غير صحيحة",
                "next": next_url,
            },
        )

    return render(
        request,
        "registration/login.html",
        {"form": LoginForm(request), "next": next_url},
    )

# ----- تسجيل الخروج -----
@login_required
def logout_view(request):
      logout(request)
      return redirect('accounts:login')


@login_required
def logout_user(request):
      try:
        session = Session.objects.get(session_key=session_key)
        session.delete()  # حذف الجلسة من قاعدة البيانات
      except Session.DoesNotExist:
        pass
