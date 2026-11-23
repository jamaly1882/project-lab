from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse
from  .form import SignupForm,UserForm,ProfileForm
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
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if next_url:
                return redirect(next_url)

            # الجميع يذهب إلى لوحة التحكم: المدير يرى كل المديريات
            # والمستخدم العادي يرى مديريته فقط.
            return redirect('masha:index')

        else:
            return render(request, "registration/login.html", {"error": "اسم المستخدم أو كلمة المرور غير صحيحة", "next": next_url})

    return render(request, "registration/login.html", {"next": next_url})

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
