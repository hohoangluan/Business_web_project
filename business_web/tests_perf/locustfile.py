"""Kịch bản load test (test_plan §4). Chạy:

    # 1) Tạo user perf (1 lần):
    python manage.py shell -c "from django.contrib.auth.models import User; from accounts.models import UserProfile; u,_=User.objects.get_or_create(username='perfuser'); u.set_password('PerfPass123!'); u.is_active=True; u.save(); UserProfile.objects.get_or_create(user=u, defaults={'employee_id':'PERF01'})"
    # 2) Chạy server:  python manage.py runserver
    # 3) Load 50:   locust -f tests_perf/locustfile.py --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8000
    #    Stress 200: locust -f tests_perf/locustfile.py --headless -u 200 -r 20 -t 60s --host http://127.0.0.1:8000
"""
import re

from locust import HttpUser, between, task


class VisitorLoad(HttpUser):
    """Tải đọc trang đăng nhập (không auth) — đo throughput stack Django."""
    wait_time = between(0.1, 0.5)

    @task
    def login_page(self):
        self.client.get("/login/")


class EmployeeJourney(HttpUser):
    """Hành trình có đăng nhập: login → dashboard → danh sách nghỉ phép."""
    wait_time = between(0.5, 1.5)

    def on_start(self):
        r = self.client.get("/login/")
        m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
        token = m.group(1) if m else ""
        self.client.post(
            "/login/",
            {"username": "perfuser", "password": "PerfPass123!",
             "csrfmiddlewaretoken": token},
            headers={"Referer": f"{self.host}/login/"},
        )

    @task(2)
    def dashboard(self):
        self.client.get("/dashboard/")

    @task(1)
    def leaves(self):
        self.client.get("/leave/")
