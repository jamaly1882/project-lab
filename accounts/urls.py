
from django.urls import path,include

from . import views 
app_name='accounts' 
urlpatterns = [
path('login', views.login_view, name='login'),
path('profile/', views.profile,name='profile'),
  path('accounts/logout/',views.logout_view, name='user_logout'),
     path('logout_user/', views.logout_user, name='logout_user'),

]

