from django.db import migrations


def backfill(apps, schema_editor):
    Report = apps.get_model('reports_interactions', 'Report')
    Report.objects.filter(is_viewed=True).update(status='acknowledged')
    Report.objects.filter(is_viewed=False).update(status='submitted')


class Migration(migrations.Migration):
    dependencies = [
        ('reports_interactions', '0005_report_manager_note_report_status'),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
