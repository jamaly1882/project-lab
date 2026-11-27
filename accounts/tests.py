"""اختبارات تسجيل الدخول ونطاق المدينة/المديرية وأدوار المساحة."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import City, Profile
from masha.models import AStmrah, Form, Mahfth, report_masahi


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

    def test_space_role_login_ignores_generic_next(self):
        """فتح الموقع من / يضيف ?next=/ للدخول؛ الدور يتقدّم على next."""
        mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        cases = (
            ("eng-next", "مهندس مساحة", "masha:show_astmrat"),
            ("head-next", "رئيس قسم مساحة", "masha:show_manager_masah_nah"),
            ("mgr-next", "مدير إدارة المساحة", "masha:screen_adrat_ver"),
            ("coord-next", "منسق قسم مساحة", "masha:interface"),
        )
        for username, role, home in cases:
            user = User.objects.create_user(username, "n@n.n", "pass1234")
            user.profile.role = role
            user.profile.mahfth = mahfth
            user.profile.save()
            for next_url in ("/", "/index/"):
                self.client.logout()
                response = self.client.post(
                    "/accounts/login/?next=" + next_url,
                    {"username": username, "password": "pass1234", "next": next_url},
                )
                self.assertRedirects(
                    response, reverse(home), msg_prefix=f"{role} next={next_url}"
                )

    def test_authenticated_space_user_opening_login_goes_to_own_profile(self):
        user = User.objects.create_user("eng-auth", "e@e.e", "pass1234")
        user.profile.role = "مهندس مساحة"
        user.profile.mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        user.profile.save()
        self.client.force_login(user)
        response = self.client.get("/accounts/login/")
        self.assertRedirects(response, reverse("masha:show_astmrat"))


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

    def test_unauthorized_user_gets_permission_page_not_template_error(self):
        self.client.force_login(self.no_scope_user)
        response = self.client.get(reverse("masha:agree_tsrah_xx"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "masha/no_permission.html")


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

    def test_head_can_open_its_approval_link(self):
        response = self.client.get(reverse("masha:agree_tsrah_xx"))
        self.assertEqual(response.status_code, 200)

    def test_head_can_open_all_links_in_its_workspace(self):
        names = (
            "masha:agree_tsrah_xx",
            "masha:serch_talbt_report_by_mnager_nah",
            "masha:show_tsrah_exit_eng_by_manger_by_manger",
            "masha:print_report",
            "masha:show_report_nah_by_manager",
            "masha:asder_nah_report_masah",
            "masha:serch_in_screen_prisdent_masah_talbt",
            "masha:serch_in_screen_prisdent_masah_talbt_to_data_base",
            "masha:show_convert_to_mashi_from_fero_nah",
            "masha:reason_rafth_managmnat_generl_to_convert_maderah",
            "masha:show_manager_masah_nah_json",
        )
        for name in names:
            if name == "masha:serch_in_screen_prisdent_masah_talbt_to_data_base":
                response = self.client.get(
                    reverse(name), {"zz": "2026-01-01", "q": "2026-01-31"}
                )
            else:
                response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_system_manager_can_open_approval_link(self):
        manager = User.objects.create_superuser("system-manager", "admin@example.com", "pass1234")
        self.client.force_login(manager)
        response = self.client.get(reverse("masha:agree_tsrah_xx"))
        self.assertEqual(response.status_code, 200)

    def test_area_manager_role_is_not_allowed_on_department_approval_link(self):
        self.user.profile.role = "مدير إدارة المساحة"
        self.user.profile.save()
        response = self.client.get(reverse("masha:agree_tsrah_xx"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "masha/no_permission.html")

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


class DirectorateDataIsolationTests(TestCase):
    """List, search, edit, and create endpoints enforce the user's directorate."""

    def setUp(self):
        self.own_mahfth = Mahfth.objects.create(name="مديرية صنعاء")
        self.other_mahfth = Mahfth.objects.create(name="مديرية عدن")
        self.user = User.objects.create_user("scoped-user", "scope@example.com", "pass1234")
        self.user.profile.role = "مهندس مساحة"
        self.user.profile.mahfth = self.own_mahfth
        self.user.profile.save()
        self.own_form = self._form("طلب صنعاء", self.own_mahfth)
        self.other_form = self._form("طلب عدن", self.other_mahfth)
        self.client.force_login(self.user)

    @staticmethod
    def _form(name, mahfth):
        return Form.objects.create(
            name=name,
            mahfth=mahfth,
            typ_aqur="",
            saft_sahb_talab="صاحب الطلب",
            streat_name="",
            content="",
            resone_refth="",
            name_wk=name,
            service_bana="",
        )

    def test_head_can_open_ready_reports_and_sees_only_own_directorate(self):
        self.user.profile.role = "رئيس قسم مساحة"
        self.user.profile.save()
        own_report = report_masahi.objects.create(
            form=self.own_form,
            return_masah_jm=True,
        )
        report_masahi.objects.create(
            form=self.other_form,
            return_masah_jm=True,
        )

        response = self.client.get(reverse("masha:show_report_nah_by_manager"))
        self.assertEqual(response.status_code, 200)
        visible_report_ids = {report.id for report in response.context["print_report_x"]}
        self.assertEqual(visible_report_ids, {own_report.id})

    def test_legacy_scoped_user_can_open_ready_reports(self):
        self.user.profile.role = ""
        self.user.profile.save()
        response = self.client.get(reverse("masha:show_report_nah_by_manager"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "masha/print_report_mashi_report_nah.html")

    def test_head_can_open_transfer_queue_with_only_own_reports(self):
        self.user.profile.role = "رئيس قسم مساحة"
        self.user.profile.save()
        own_report = report_masahi.objects.create(
            form=self.own_form,
            agree_adarah_generl_by_manager_mahfth=True,
        )
        report_masahi.objects.create(
            form=self.other_form,
            agree_adarah_generl_by_manager_mahfth=True,
        )

        response = self.client.get(reverse("masha:show_convert_to_mashi_from_fero_nah"))
        self.assertEqual(response.status_code, 200)
        visible_report_ids = {report.id for report in response.context["show_manger_form"]}
        self.assertEqual(visible_report_ids, {own_report.id})

    def test_head_transfer_marks_report_moved_and_removes_it_from_queue(self):
        self.user.profile.role = "رئيس قسم مساحة"
        self.user.profile.save()
        report = report_masahi.objects.create(
            form=self.own_form,
            agree_adarah_generl_by_manager_mahfth=True,
        )

        response = self.client.post(
            reverse("masha:agree_report_masahi_by_manager_mangmant_adarah", args=[report.id]),
            {"exit": "منجزة", "text36": "تم الترحيل"},
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertTrue(report.masahi_convert)
        self.assertTrue(report.agree_adarah_generl_by_manager_mahfth)

        queue_response = self.client.get(reverse("masha:show_convert_to_mashi_from_fero_nah"))
        self.assertEqual(queue_response.status_code, 200)
        self.assertNotIn(report.id, {item.id for item in queue_response.context["show_manger_form"]})

    def test_legacy_scoped_user_can_open_transfer_queue(self):
        self.user.profile.role = ""
        self.user.profile.save()
        response = self.client.get(reverse("masha:show_convert_to_mashi_from_fero_nah"))
        self.assertEqual(response.status_code, 200)

    def test_engineer_ajax_search_only_returns_own_directorate(self):
        response = self.client.get(reverse("masha:live_search_ajax_hadod_a"), {"q": "طلب"})
        self.assertEqual(response.status_code, 200)
        result_ids = {item["id"] for item in response.json()["results"]}
        self.assertIn(self.own_form.id, result_ids)
        self.assertNotIn(self.other_form.id, result_ids)

    def test_engineer_cannot_open_another_directorates_edit_form(self):
        response = self.client.get(
            reverse("masha:search_edit_form_talb", args=[self.other_form.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_engineer_cannot_post_another_directorates_edit(self):
        response = self.client.post(
            reverse("masha:edit_form_talb", args=[self.other_form.id]),
            {"card_id": "1", "name": "modified", "phone": "1", "typ": ""},
        )
        self.assertEqual(response.status_code, 404)
        self.other_form.refresh_from_db()
        self.assertEqual(self.other_form.name, "طلب عدن")

    def test_engineer_cannot_edit_another_directorates_ajax_report(self):
        response = self.client.post(
            reverse("masha:edit_report_ajax", args=[self.other_form.id]),
            {"name": "modified"},
        )
        self.assertEqual(response.status_code, 404)
        self.other_form.refresh_from_db()
        self.assertEqual(self.other_form.name, "طلب عدن")

    def test_coordinator_report_list_only_shows_own_directorate(self):
        self.user.profile.role = "منسق قسم مساحة"
        self.user.profile.save()
        for obj in (self.own_form, self.other_form):
            obj.show_tasrah_karoj = True
            obj.hidden_ansh_hdm = "استشارة"
            obj.save()
        response = self.client.get(reverse("masha:show_tsrah_exit_eng_by_manger_astsherh"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "طلب صنعاء")
        self.assertNotContains(response, "طلب عدن")

    def test_coordinator_cannot_create_request_in_another_directorate(self):
        self.user.profile.role = "منسق قسم مساحة"
        self.user.profile.save()
        response = self.client.post(
            reverse("masha:form_add_masah_nah"),
            {
                "hid_mah": self.other_mahfth.id,
                "name_aml": "طلب جديد",
                "hid_type_form_rakash": "صاحب الطلب",
                "hid_type_aqure": "",
                "streat_name": "",
                "content": "",
                "resone_refth": "",
                "f2": "مقدم الطلب",
                "f4": "000",
                "f6": "000",
                "hid_ansh_hdm": "",
                "service_bana": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        created_form = Form.objects.exclude(id__in=[self.own_form.id, self.other_form.id]).get()
        self.assertEqual(created_form.mahfth_id, self.own_mahfth.id)


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
