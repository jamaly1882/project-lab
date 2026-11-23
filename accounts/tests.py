"""اختبارات تسجيل الدخول ونطاق المدينة/المديرية."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import City
from masha.models import AStmrah, Mahfth


class LoginPageTests(TestCase):
    """صفحة الدخول يجب أن تعرض حقلي اسم المستخدم وكلمة المرور دائماً."""

    def test_login_page_has_username_and_password_fields(self):
        for url in ("/accounts/login/", "/accounts/login"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            body = response.content.decode()
            self.assertIn('id="id_username"', body, url)
            self.assertIn('id="id_password"', body, url)

    def test_login_page_uses_custom_view(self):
        # /accounts/login/ يجب أن تستخدم العرض المخصّص (وليس LoginView الافتراضي)
        from accounts.views import login_view

        self.assertEqual(reverse("accounts:login"), "/accounts/login/")
        response = self.client.get("/accounts/login/")
        self.assertTemplateUsed(response, "registration/login.html")

    def test_successful_login_redirects_to_dashboard(self):
        User.objects.create_user("tester", "t@t.t", "pass1234")
        response = self.client.post(
            "/accounts/login/", {"username": "tester", "password": "pass1234"}
        )
        self.assertRedirects(response, "/index/")

    def test_wrong_password_shows_arabic_error(self):
        User.objects.create_user("tester", "t@t.t", "pass1234")
        response = self.client.post(
            "/accounts/login/", {"username": "tester", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "غير صحيحة")


class CityScopeTests(TestCase):
    """روابط وبيانات المستخدم تتبع مدينته/مديريته."""

    def setUp(self):
        self.m1 = Mahfth.objects.create(name="مديرية صنعاء")
        self.m2 = Mahfth.objects.create(name="مديرية عدن")
        AStmrah.objects.get_or_create(id=1, defaults={"name": "نموذج"})
        AStmrah.objects.get_or_create(id=2, defaults={"name": "نموذج 2"})

        self.manager = User.objects.create_superuser("mgr", "m@m.m", "pass1234")
        self.user = User.objects.create_user("usr", "u@u.u", "pass1234")
        self.user.profile.mahfth = self.m2
        self.user.profile.save()

        self.city_user = User.objects.create_user("city", "c@c.c", "pass1234")
        city = City.objects.create(city="مدينة صنعاء", phone_number="1", mahfth=self.m1)
        profile = self.city_user.profile
        profile.city = city
        profile.mahfth = self.m1
        profile.save()

        self.no_scope_user = User.objects.create_user("nom", "n@n.n", "pass1234")

    def test_manager_sees_all_directorates(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("masha:enter_data_report_masahi"))
        body = response.content.decode()
        self.assertIn("مديرية صنعاء", body)
        self.assertIn("مديرية عدن", body)

    def test_user_sees_only_own_directorate(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("masha:enter_data_report_masahi"))
        body = response.content.decode()
        start = body.find('id="mderah"')
        segment = body[start : start + 900]
        self.assertIn("مديرية عدن", segment)
        self.assertNotIn("مديرية صنعاء", segment)

    def test_city_user_sees_own_city_badge(self):
        self.client.force_login(self.city_user)
        response = self.client.get(reverse("masha:interface"))
        self.assertContains(response, "مدينة صنعاء")

    def test_user_without_scope_sees_no_section_tiles(self):
        self.client.force_login(self.no_scope_user)
        response = self.client.get(reverse("masha:interface"))
        body = response.content.decode()
        self.assertNotIn("ادارة المساحة", body)
        self.assertNotIn("قسم المساحة", body)

    def test_user_with_scope_can_open_section_screens(self):
        self.client.force_login(self.user)
        for name in (
            "masha:astshr",
            "masha:screen_adrat_ver",
            "masha:show_astmrat",
            "masha:show_managment_nah",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_user_without_scope_is_redirected_with_message(self):
        self.client.force_login(self.no_scope_user)
        response = self.client.get(reverse("masha:show_astmrat"), follow=True)
        self.assertRedirects(response, "/index/")
        self.assertContains(response, "لم يتم ربط حسابك")
