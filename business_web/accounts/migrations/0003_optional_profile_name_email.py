from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def clear_pending_email_values(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")

    for profile in UserProfile.objects.filter(email__iendswith="@pending.local"):
        old_email = profile.email or ""
        profile.email = None
        profile.save(update_fields=["email"])

        if old_email:
            User.objects.filter(pk=profile.user_id, email__iexact=old_email).update(email="")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0002_split_personal_info"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="permissions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Custom permissions assigned independently from role.",
                related_name="users",
                to="accounts.custompermission",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="role",
            field=models.ForeignKey(
                blank=True,
                help_text="System role used for interface and access control.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="users",
                to="accounts.role",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="user",
            field=models.OneToOneField(
                help_text="Django user that owns this profile.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="userprofile",
            name="userprofile_full_name_not_blank",
        ),
        migrations.RemoveConstraint(
            model_name="userprofile",
            name="userprofile_email_not_blank",
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="full_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Full name from registration.",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="email",
            field=models.EmailField(
                blank=True,
                help_text="Email from registration.",
                max_length=254,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(clear_pending_email_values, migrations.RunPython.noop),
    ]
