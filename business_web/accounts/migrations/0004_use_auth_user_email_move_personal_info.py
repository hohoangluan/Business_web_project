from django.db import migrations


def copy_profile_email_to_user(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")

    profiles = (
        UserProfile.objects.select_related("user")
        .exclude(email__isnull=True)
        .exclude(email="")
    )
    for profile in profiles:
        user = profile.user
        if not user.email:
            user.email = profile.email
            user.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("employee_profiles", "0002_personal_info"),
        ("accounts", "0003_optional_profile_name_email"),
    ]

    operations = [
        migrations.RunPython(copy_profile_email_to_user, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="userprofile",
            name="email",
        ),
        migrations.DeleteModel(
            name="PersonalInfo",
        ),
    ]
