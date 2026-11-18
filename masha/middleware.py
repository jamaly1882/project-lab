# masha/middleware.py

from django.shortcuts import redirect
from django.urls import reverse

class PreventBackAfterLogoutMiddleware:
    """
    يمنع الوصول إلى الصفحات المحمية بعد تسجيل الخروج.
    ويضيف هيدرز تمنع تخزين الصفحة في الكاش.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # تطبيق الهيدرز لمنع الكاش لجميع الصفحات
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        # لو الصفحة محمية ولم يسجل المستخدم الدخول → تحويله للـ login
        if request.user.is_authenticated is False:
            protected_paths = [
                reverse('masha:interface'),
                # أضف كل أسماء المسارات المحمية هنا
            ]
            if request.path in protected_paths:
                return redirect('accounts:login')

        return response
