import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_personal_info_from_accounts(apps, schema_editor):
    OldPersonalInfo = apps.get_model("accounts", "PersonalInfo")
    NewPersonalInfo = apps.get_model("employee_profiles", "PersonalInfo")

    for old_info in OldPersonalInfo.objects.all():
        NewPersonalInfo.objects.update_or_create(
            user_id=old_info.user_profile.user_id,
            defaults={
                "phone_number": old_info.phone_number or "",
                "date_of_birth": old_info.date_of_birth or "",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0003_optional_profile_name_email"),
        ("employee_profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonalInfo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Phone number.",
                        max_length=20,
                    ),
                ),
                (
                    "date_of_birth",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Date of birth (DD/MM/YYYY).",
                        max_length=10,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        help_text="User that owns this personal information.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_info",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["user__username"],
            },
        ),
        migrations.RunPython(copy_personal_info_from_accounts, migrations.RunPython.noop),
    ]
