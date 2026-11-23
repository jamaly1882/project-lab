
from django.urls import path,include

from . import views 
from . import user_views
app_name='accounts' 
urlpatterns = [
path('login/', views.login_view, name='login'),
     # اسم بديل بدون شرطة أخيرة (لروابط قديمة مثل /accounts/login)
     path('login', views.login_view, name='login_no_slash'),
path('profile/', views.profile,name='profile'),
  path('accounts/logout/',views.logout_view, name='user_logout'),
     path('logout_user/', views.logout_user, name='logout_user'),

     # ===== إدارة المستخدمين (مدير النظام) =====
     path('users/', user_views.user_manage, name='user_manage'),
     path('users/<int:pk>/edit/', user_views.user_edit, name='user_edit'),
     path('users/<int:pk>/toggle/', user_views.user_toggle_active, name='user_toggle_active'),
     path('users/<int:pk>/delete/', user_views.user_delete, name='user_delete'),

]

