"""اختبارات تسجيل الدخول ونطاق المدينة/المديرية وأدوار المساحة."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import City, Profile
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
        response = self.client.get("/accounts/login/")
        self.assertEqual(reverse("accounts:login"), "/accounts/login/")
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

    def test_space_role_login_opens_own_profile(self):
        user = User.objects.create_user("surveyor", "s@s.s", "pass1234")
        user.profile.role = "مهندس مساحة"
        user.profile.mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        user.profile.save()
        response = self.client.post(
            "/accounts/login/", {"username": "surveyor", "password": "pass1234"}
        )
        self.assertRedirects(response, reverse("masha:show_astmrat"))

    def test_coordinator_login_opens_report_services(self):
        user = User.objects.create_user("coordinator", "c@s.s", "pass1234")
        user.profile.role = "منسق قسم مساحة"
        user.profile.mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        user.profile.save()
        response = self.client.post(
            "/accounts/login/", {"username": "coordinator", "password": "pass1234"}
        )
        self.assertRedirects(response, reverse("masha:interface"))


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

    def test_user_without_coordinator_role_cannot_open_report_issue_form(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("masha:enter_data_report_masahi"))
        self.assertRedirects(response, reverse("masha:index"))

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

    def test_unassigned_user_cannot_open_report_entry_screens(self):
        self.client.force_login(self.user)
        for name in ("masha:astshr", "masha:interface_nah_astshr", "masha:enter_data_report_masahi_screen"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)

    def test_unassigned_user_can_open_legacy_space_sections(self):
        self.client.force_login(self.user)
        for name in (
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


class SpaceRoleAccessTests(TestCase):
    def setUp(self):
        self.mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        self.user = User.objects.create_user("head", "h@h.h", "pass1234")
        self.user.profile.role = Profile.ROLE_CHOICES[0][0]
        self.user.profile.mahfth = self.mahfth
        self.user.profile.save()
        self.client.force_login(self.user)

    def test_head_user_is_taken_to_profile_without_showing_role_icons(self):
        response = self.client.get(reverse("masha:interface"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("masha:screen_adrat_ver"))
        self.assertNotContains(response, reverse("masha:screen_paesdint_masah"))
        self.assertNotContains(response, reverse("masha:enter_data_report_masahi_screen"))
        response = self.client.get(reverse("masha:screen_paesdint_masah"))
        self.assertRedirects(response, reverse("masha:show_manager_masah_nah"))

    def test_role_user_is_blocked_from_space_management_and_its_links(self):
        for name in (
            "masha:screen_adrat_ver",
            "masha:show_managment_nah",
            "masha:show_convert_to_mashi_from_fero",
            "masha:show_convert_to_mashi_from_fero_nah_adrah",
            "masha:rafth_by_manager_aldarah_generl_nah",
            "masha:show_conecctions",
            "masha:realtime_counts",
            "masha:screen_enter_number_mahther_and_number_strate_and_unit",
        ):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, reverse("masha:show_manager_masah_nah"), msg_prefix=name)

    def test_head_is_redirected_directly_to_its_own_profile(self):
        response = self.client.get(reverse("masha:screen_paesdint_masah"))
        self.assertRedirects(response, reverse("masha:show_manager_masah_nah"))

    def test_head_cannot_open_engineer_profile(self):
        response = self.client.get(reverse("masha:show_astmrat"))
        self.assertRedirects(response, reverse("masha:show_manager_masah_nah"))
        response = self.client.get(reverse("masha:show_manager_masah_nah"))
        self.assertEqual(response.status_code, 200)

    def test_coordinator_can_open_both_report_workflows(self):
        self.user.profile.role = "منسق قسم مساحة"
        self.user.profile.save()
        AStmrah.objects.get_or_create(id=1, defaults={"name": "تقرير البناء"})
        AStmrah.objects.get_or_create(id=2, defaults={"name": "تقرير الاستشارة"})

        response = self.client.get(reverse("masha:interface"))
        self.assertContains(response, reverse("masha:enter_data_report_masahi_screen"))
        self.assertContains(response, reverse("masha:interface_nah_astshr"))
        self.assertNotContains(response, reverse("masha:screen_adrat_ver"))

        for name in (
            "masha:enter_data_report_masahi_screen",
            "masha:enter_data_report_masahi",
            "masha:interface_nah_astshr",
            "masha:astshr",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            if name in {"masha:enter_data_report_masahi", "masha:astshr"}:
                self.assertContains(
                    response,
                    'id="hid_mah" value="{}"'.format(self.mahfth.pk),
                    html=False,
                )

    def test_head_is_denied_both_report_workflows(self):
        for name in (
            "masha:enter_data_report_masahi_screen",
            "masha:enter_data_report_masahi",
            "masha:interface_nah_astshr",
            "masha:astshr",
        ):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, reverse("masha:show_manager_masah_nah"), msg_prefix=name)


class UserRoleFormTests(TestCase):
    def test_add_user_form_orders_english_username_and_passwords_from_right(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "pass1234")
        self.client.force_login(admin)
        response = self.client.get(reverse("accounts:user_manage"))
        body = response.content.decode()
        username_pos = body.index('id="id_username"')
        password_pos = body.index('id="id_password1"')
        confirm_pos = body.index('id="id_password2"')
        self.assertLess(username_pos, password_pos)
        self.assertLess(password_pos, confirm_pos)
        self.assertIn('dir="ltr"', body[username_pos - 120 : username_pos + 40])
        self.assertContains(response, 'name="role" class="form-control" dir="rtl"')
        self.assertContains(response, "مدير إدارة المساحة")

    def test_admin_can_assign_a_role_instead_of_city(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "pass1234")
        mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        self.client.force_login(admin)
        response = self.client.post(
            reverse("accounts:user_manage"),
            {
                "username": "new-surveyor",
                "password1": "pass1234",
                "password2": "pass1234",
                "mahfth": mahfth.pk,
                "role": "مهندس مساحة",
                "phone_number": "777000000",
                "first_name": "مهندس",
                "last_name": "مساحة",
                "email": "surveyor@example.com",
            },
        )
        self.assertRedirects(response, reverse("accounts:user_manage"))
        created = User.objects.get(username="new-surveyor")
        self.assertEqual(created.profile.role, "مهندس مساحة")
        self.assertIsNone(created.profile.city)

    def test_area_manager_role_does_not_require_directorate_and_can_open_its_page(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "pass1234")
        self.client.force_login(admin)
        response = self.client.post(
            reverse("accounts:user_manage"),
            {
                "username": "area-manager",
                "password1": "pass1234",
                "password2": "pass1234",
                "mahfth": "",
                "role": "مدير إدارة المساحة",
                "phone_number": "",
            },
        )
        self.assertRedirects(response, reverse("accounts:user_manage"))
        area_manager = User.objects.get(username="area-manager")
        self.assertEqual(area_manager.profile.role, "مدير إدارة المساحة")
        self.assertIsNone(area_manager.profile.mahfth)

        self.client.force_login(area_manager)
        response = self.client.get(reverse("masha:screen_adrat_ver"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("masha:interface"))
        self.assertNotContains(response, reverse("masha:screen_adrat_ver"))

        self.client.logout()
        response = self.client.post(
            "/accounts/login/",
            {"username": "area-manager", "password": "pass1234"},
        )
        self.assertRedirects(response, reverse("masha:screen_adrat_ver"))

    def test_other_roles_still_require_directorate(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "pass1234")
        self.client.force_login(admin)
        response = self.client.post(
            reverse("accounts:user_manage"),
            {
                "username": "surveyor-no-scope",
                "password1": "pass1234",
                "password2": "pass1234",
                "mahfth": "",
                "role": "مهندس مساحة",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اختيار المديرية مطلوب لهذا الدور")
        self.assertFalse(User.objects.filter(username="surveyor-no-scope").exists())
