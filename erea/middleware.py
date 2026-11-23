"""وسيط خاص ببيئة المعاينة (preview).

الغرض:
    * السماح بعرض صفحات النظام داخل إطار (iframe) في بيئة المعاينة فقط،
      لأن المتصفح على نطاق مختلف عن نطاق السيرفر.
    * إضافة نطاق الطلب الحالي إلى CSRF_TRUSTED_ORIGINS عند الوصول عبر
      بروكسي المعاينة (https://<port>-<sandbox>.e2b.app) حتى تعمل
      نماذج POST (تسجيل الدخول، إضافة مستخدم ...).

ما لا يفعله:
    * لا يغيّر أي إعداد عند التشغيل المحلي العادي (127.0.0.1 / localhost).
"""

from django.conf import settings


PREVIEW_SUFFIXES = (".e2b.app", ".e2b.dev", ".e2b.local")


def _is_preview_host(host):
    host = (host or "").split(":")[0].lower()
    return any(host.endswith(suffix) or host == suffix.lstrip(".") for suffix in PREVIEW_SUFFIXES)


class PreviewEmbedMiddleware:
    """يسمح بعرض الصفحات داخل iframe عند الوصول من نطاق المعاينة فقط."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host() if request.META.get("HTTP_HOST") else ""
        if _is_preview_host(host):
            # اجعل Django يقبل الطلب بغض النظر عن منفذ البروكسي
            if host and host not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(host)

            # اسمح بـ POST من نفس النطاق (مع الحفاظ على فحص الـ CSRF token)
            origin = f"{request.scheme}://{request.get_host()}"
            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                settings.CSRF_TRUSTED_ORIGINS.append(origin)

        response = self.get_response(request)

        if _is_preview_host(host):
            # لا يمكن التحقق من origin داخل ساندبوكس المعاينة، لذا نزيل
            # رأس الرفض ونستخدم سياسة الأصدقاء لنفس الموقع.
            response.headers.pop("X-Frame-Options", None)
            response.headers["Content-Security-Policy"] = "frame-ancestors *"

        return response
