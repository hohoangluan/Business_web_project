"""Admin config for employee profile detail models."""

from django.contrib import admin

from employee_profiles.models import PersonalInfo


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "date_of_birth")
    search_fields = (
        "user__username",
        "user__email",
        "user__profile__employee_id",
        "phone_number",
    )
