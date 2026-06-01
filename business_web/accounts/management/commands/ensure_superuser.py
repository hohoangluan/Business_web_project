"""Tạo (hoặc cập nhật) superuser từ biến môi trường — chạy idempotent.

Dùng cho deploy không có shell (vd Render free). Gọi trong build.sh.
Đọc env:
    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_EMAIL      (tùy chọn)
    DJANGO_SUPERUSER_PASSWORD

Không có đủ username + password -> bỏ qua, không lỗi (build vẫn pass).
Đã tồn tại -> đảm bảo is_staff/is_superuser=True và reset password.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Tạo/cập nhật superuser từ env (idempotent).'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write(
                'ensure_superuser: thiếu DJANGO_SUPERUSER_USERNAME/PASSWORD '
                '-> bỏ qua.'
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email},
        )
        user.is_staff = True
        user.is_superuser = True
        if email:
            user.email = email
        user.set_password(password)
        user.save()

        verb = 'Tạo mới' if created else 'Cập nhật'
        self.stdout.write(self.style.SUCCESS(
            f'ensure_superuser: {verb} superuser "{username}".'
        ))
