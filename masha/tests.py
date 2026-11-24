"""اختبارات انتقال التقارير بين قوائم الإدارة ورئيس القسم."""

import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from .models import Form, Mahfth, report_masahi


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ReportApprovalFlowTests(TestCase):
    def setUp(self):
        self.mahfth = Mahfth.objects.create(name="مديرية الاختبار")
        self.form = Form.objects.create(
            name="قطعة اختبار",
            mahfth=self.mahfth,
            kml_file=SimpleUploadedFile("test.kml", b"<kml/>"),
        )
        self.report = report_masahi.objects.create(
            name="مساحي",
            form=self.form,
            kml_file=SimpleUploadedFile("report.kml", b"<kml/>"),
            agree_adarah_generl_by_manager_mahfth=True,
        )
        self.url = reverse(
            "masha:agree_report_masahi_by_manager_mangmant_adarah",
            args=[self.report.pk],
        )

    @staticmethod
    def _make_manager(username):
        return User.objects.create_user(username, password="pass12345", is_staff=True)

    def _make_head(self, username, mahfth):
        user = User.objects.create_user(username, password="pass12345")
        # إشارة post_save تنشئ Profile تلقائياً عند إنشاء المستخدم.
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.mahfth = mahfth
        profile.save()
        return user

    def test_head_approval_moves_report_to_ready_reports(self):
        """موافقة رئيس القسم تُخرج التقرير من قوائم الانتظار وتُظهره في الجاهزة."""
        head = self._make_head("head1", self.mahfth)
        self.client.force_login(head)

        response = self.client.post(
            self.url, {"exit": "منجزة", "text36": "تمت الموافقة", "no_salm_5": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertTrue(self.report.return_masah_jm)
        self.assertFalse(self.report.masahi_convert)
        # علم الموافقة محفوظ حتى تبقى المعاملة في قائمة مدير الإدارة العامة.
        self.assertTrue(self.report.agree_adarah_generl_by_manager_mahfth)
        self.assertFalse(self.report.rafth_adarah_generl_by_manager_mahfth)
        self.assertEqual(self.report.ajaml, "تمت الموافقة")

        # يختفي من قائمة رئيس القسم، ويبقى في قوائم مدير الإدارة العامة.
        pending = self.client.get(
            reverse("masha:show_convert_to_mashi_from_fero_nah")
        ).context["show_manger_form"]
        self.assertNotIn(self.report, pending)
        self.client.logout()
        self.client.force_login(self._make_manager("manager6"))
        management_list = self.client.get(
            reverse("masha:show_convert_to_mashi_from_fero_nah_adrah")
        ).context["show_manger_form"]
        self.assertIn(self.report, management_list)
        self.client.logout()
        self.client.force_login(head)

        ready = report_masahi.objects.filter(
            return_masah_jm=True,
            rafth_adarah_generl=False,
            masahi_convert=False,
            rafth_adarah_generl_by_manager_mahfth=False,
        )
        self.assertIn(self.report, ready)
        ready_page = self.client.get(reverse("masha:show_report_nah_by_manager"))
        self.assertIn(self.report, ready_page.context["print_report_x"])

    def test_manager_approval_keeps_report_in_management_list(self):
        """موافقة مدير الإدارة تُبقي علم الموافقة محفوظاً لقائمة الإدارة العامة."""
        self.client.force_login(self._make_manager("manager2"))

        response = self.client.post(self.url, {"exit": "منجزة", "text36": ""})

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertTrue(self.report.agree_adarah_generl_by_manager_mahfth)
        self.assertFalse(self.report.masahi_convert)
        self.assertFalse(self.report.return_masah_jm)

        management_list = self.client.get(
            reverse("masha:show_convert_to_mashi_from_fero_nah_adrah")
        ).context["show_manger_form"]
        self.assertIn(self.report, management_list)

    def test_rejection_keeps_report_out_of_ready_reports(self):
        self.client.force_login(self._make_manager("manager3"))

        response = self.client.post(
            self.url, {"exit": "رفض", "no_salm_5": "تعديل مطلوب", "text36": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertTrue(self.report.rafth_adarah_generl_by_manager_mahfth)
        self.assertFalse(self.report.return_masah_jm)
        self.assertFalse(self.report.agree_adarah_generl_by_manager_mahfth)
        self.assertEqual(self.report.resone_refth_adrah, "تعديل مطلوب")

    def test_head_cannot_approve_report_from_another_mahfth(self):
        other_mahfth = Mahfth.objects.create(name="مديرية أخرى")
        self.client.force_login(self._make_head("head2", other_mahfth))

        response = self.client.post(self.url, {"exit": "منجزة"})

        self.assertEqual(response.status_code, 404)
        self.report.refresh_from_db()
        self.assertFalse(self.report.masahi_convert)
        self.assertFalse(self.report.return_masah_jm)

    def test_missing_action_is_rejected(self):
        self.client.force_login(self._make_manager("manager4"))
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_sector_column_is_hidden_in_list_tables(self):
        """عمود «القطاع» لا يظهر في جداول العرض الخاصة بالتقارير."""
        self.client.force_login(
            User.objects.create_superuser("admin5", "admin5@example.com", "pass12345")
        )
        for url_name in (
            "masha:show_convert_to_mashi_from_fero_nah_adrah",
            "masha:show_convert_to_mashi_from_fero",
            "masha:print_report",
        ):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)
            self.assertNotContains(response, "القطاع", msg_prefix=url_name)

    def test_management_screen_keeps_reports_for_non_staff_manager(self):
        """الموافقة من شاشة الإدارة العامة تبقى المعاملة في قوائم المدير."""
        head = self._make_head("manager_screen_user", self.mahfth)
        self.client.force_login(head)

        response = self.client.post(
            self.url, {"exit": "منجزة", "space": "management", "text36": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertTrue(self.report.agree_adarah_generl_by_manager_mahfth)
        self.assertFalse(self.report.return_masah_jm)
        management_list = self.client.get(
            reverse("masha:show_convert_to_mashi_from_fero_nah_adrah")
        ).context["show_manger_form"]
        self.assertIn(self.report, management_list)

    def test_management_dashboard_keeps_three_sections(self):
        """صفحة مدير الإدارة العامة تعرض الوارد والمقبول والمرفوض."""
        self.client.force_login(self._make_manager("manager7"))
        for url_name in ("masha:show_managment_nah", "masha:screen_adrat_ver"):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)
            body = response.content.decode()
            for section in ("الوارد من الفروع", "المقبولة من الادارة", "المرفوضة من  الادارة"):
                self.assertIn(section, body, url_name)
            self.assertIn("num_unread_1", response.context or {}, url_name)

    def test_report_detail_passes_approval_screen(self):
        head = self._make_head("head3", self.mahfth)
        self.client.force_login(head)
        response = self.client.get(
            reverse("masha:show_report_adrah", args=[self.report.pk]) + "?space=head"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="approval_space"')
        self.assertContains(response, 'value="head"')

    def test_head_lists_are_limited_to_his_mahfth(self):
        """الجاهزة والمقبولة من الإدارة تعرضان مديرية رئيس القسم فقط."""
        other_mahfth = Mahfth.objects.create(name="مديرية أخرى للعرض")
        other_form = Form.objects.create(
            name="قطعة أخرى",
            mahfth=other_mahfth,
            kml_file=SimpleUploadedFile("other.kml", b"<kml/>"),
        )
        other_report = report_masahi.objects.create(
            name="مساحي",
            form=other_form,
            kml_file=SimpleUploadedFile("other-report.kml", b"<kml/>"),
            return_masah_jm=True,
            agree_adarah_generl_by_manager_mahfth=True,
        )

        head = self._make_head("head_scope", self.mahfth)
        self.client.force_login(head)

        # التقارير الجاهزة
        self.report.return_masah_jm = True
        self.report.save()
        ready = self.client.get(
            reverse("masha:show_report_nah_by_manager")
        ).context["print_report_x"]
        self.assertIn(self.report, ready)
        self.assertNotIn(other_report, ready)

        # المقبولة من الإدارة (يجب ألا يكون التقرير جاهزاً حتى يظهر هنا)
        self.report.return_masah_jm = False
        self.report.save()
        accepted = self.client.get(
            reverse("masha:show_convert_to_mashi_from_fero_nah")
        ).context["show_manger_form"]
        self.assertIn(self.report, accepted)
        self.assertNotIn(other_report, accepted)

        # مدير النظام يرى مديريات كلها في القائمتين
        self.client.logout()
        self.client.force_login(self._make_manager("manager_scope"))
        all_ready = self.client.get(
            reverse("masha:show_report_nah_by_manager")
        ).context["print_report_x"]
        self.assertIn(other_report, all_ready)
