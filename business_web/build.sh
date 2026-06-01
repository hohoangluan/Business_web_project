#!/usr/bin/env bash
# Render build script. Chạy mỗi lần deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# Tạo superuser từ env (idempotent, bỏ qua nếu thiếu env) — thay cho Render Shell.
python manage.py ensure_superuser
