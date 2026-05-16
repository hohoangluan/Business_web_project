import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def unique_value(model, field_name, base_value, current_pk):
    base_value = (base_value or "").strip() or f"profile-{current_pk}"
    candidate = base_value
    suffix = 1
    lookup = {f"{field_name}__iexact": candidate}
    while model.objects.exclude(pk=current_pk).filter(**lookup).exists():
        candidate = f"{base_value}-{suffix}"
        lookup = {f"{field_name}__iexact": candidate}
        suffix += 1
    return candidate


def unique_email(UserProfile, base_email, employee_id, current_pk):
    base_email = (base_email or "").strip()
    if not base_email:
        base_email = f"{employee_id}@pending.local"

    local_part, _, domain = base_email.partition("@")
    if not domain:
        local_part = employee_id
        domain = "pending.local"

    candidate = f"{local_part}@{domain}"
    suffix = 1
    while UserProfile.objects.exclude(pk=current_pk).filter(email__iexact=candidate).exists():
        candidate = f"{local_part}-{suffix}@{domain}"
        suffix += 1
    return candidate


def fill_required_user_profile_fields(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")

    for profile in UserProfile.objects.select_related("user").all():
        user = profile.user
        employee_id = unique_value(
            UserProfile,
            "employee_id",
            profile.employee_id or user.username,
            profile.pk,
        )
        full_name = (profile.full_name or "").strip()
        if not full_name:
            full_name = " ".join(
                part for part in [user.first_name, user.last_name] if part
            ).strip()
        if not full_name:
            full_name = employee_id

        email = unique_email(
            UserProfile,
            profile.email or user.email,
            employee_id,
            profile.pk,
        )

        profile.employee_id = employee_id
        profile.full_name = full_name
        profile.email = email
        profile.save(update_fields=["employee_id", "full_name", "email"])


def create_personal_info_records(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    PersonalInfo = apps.get_model("accounts", "PersonalInfo")

    for profile in UserProfile.objects.all():
        PersonalInfo.objects.get_or_create(
            user_profile=profile,
            defaults={
                "phone_number": profile.phone_number or "",
                "date_of_birth": profile.date_of_birth or "",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.RunPython(fill_required_user_profile_fields, migrations.RunPython.noop),
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
                    "user_profile",
                    models.OneToOneField(
                        db_column="employee_id",
                        help_text="User profile linked by employee ID.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_info",
                        to="accounts.userprofile",
                        to_field="employee_id",
                    ),
                ),
            ],
            options={
                "ordering": ["user_profile__user__username"],
            },
        ),
        migrations.RunPython(create_personal_info_records, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="userprofile",
            name="phone_number",
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="date_of_birth",
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="employee_id",
            field=models.CharField(
                help_text="Unique employee ID.",
                max_length=50,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="full_name",
            field=models.CharField(
                help_text="Full name from registration.",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="email",
            field=models.EmailField(
                help_text="Email from registration.",
                max_length=254,
                unique=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="userprofile",
            constraint=models.CheckConstraint(
                check=~Q(employee_id=""),
                name="userprofile_employee_id_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="userprofile",
            constraint=models.CheckConstraint(
                check=~Q(full_name=""),
                name="userprofile_full_name_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="userprofile",
            constraint=models.CheckConstraint(
                check=~Q(email=""),
                name="userprofile_email_not_blank",
            ),
        ),
    ]
