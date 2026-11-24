from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_auto_20261123_2104"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="role",
            field=models.CharField(
                blank=True,
                choices=[
                    ("رئيس قسم مساحة", "رئيس قسم مساحة"),
                    ("مهندس مساحة", "مهندس مساحة"),
                    ("منسق قسم مساحة", "منسق قسم مساحة"),
                ],
                default="",
                max_length=50,
                verbose_name="الدور",
            ),
        ),
    ]
