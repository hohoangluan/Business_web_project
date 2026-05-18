from django.db import migrations

def populate_default_categories(apps, schema_editor):
    EvaluationCategory = apps.get_model('performance', 'EvaluationCategory')
    categories = [
        ('Chuyên cần', 'Đánh giá mức độ đi làm đúng giờ, tuân thủ lịch làm việc'),
        ('Hiệu suất công việc', 'Năng suất, chất lượng đầu ra, hoàn thành KPI/mục tiêu'),
        ('Kỹ năng làm việc nhóm', 'Tinh thần phối hợp, hỗ trợ đồng nghiệp, giao tiếp nội bộ'),
        ('Thái độ & Ý thức', 'Thái độ làm việc, tính chủ động, tinh thần cầu tiến'),
        ('Sáng tạo & Đổi mới', 'Đề xuất cải tiến, giải quyết vấn đề sáng tạo'),
        ('Tuân thủ nội quy', 'Chấp hành quy định công ty, văn hóa doanh nghiệp'),
        ('Phát triển chuyên môn', 'Học hỏi, nâng cao kỹ năng, đạt chứng chỉ trong kỳ'),
    ]
    for name, desc in categories:
        EvaluationCategory.objects.get_or_create(name=name, defaults={'description': desc})

def remove_default_categories(apps, schema_editor):
    EvaluationCategory = apps.get_model('performance', 'EvaluationCategory')
    names = [
        'Chuyên cần', 'Hiệu suất công việc', 'Kỹ năng làm việc nhóm',
        'Thái độ & Ý thức', 'Sáng tạo & Đổi mới', 'Tuân thủ nội quy',
        'Phát triển chuyên môn'
    ]
    EvaluationCategory.objects.filter(name__in=names).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0002_evaluationcategory_evaluation_acknowledged_at_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_default_categories, remove_default_categories),
    ]
