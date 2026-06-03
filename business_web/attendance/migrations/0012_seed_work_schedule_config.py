from datetime import time

from django.db import migrations


def seed_config(apps, schema_editor):
    WorkScheduleConfig = apps.get_model('attendance', 'WorkScheduleConfig')
    WorkScheduleConfig.objects.get_or_create(
        pk=1,
        defaults={
            'shift_start': time(8, 30),
            'shift_end': time(17, 30),
            'late_grace_minutes': 5,
        },
    )


def unseed_config(apps, schema_editor):
    WorkScheduleConfig = apps.get_model('attendance', 'WorkScheduleConfig')
    WorkScheduleConfig.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0011_workscheduleconfig'),
    ]

    operations = [
        migrations.RunPython(seed_config, unseed_config),
    ]
