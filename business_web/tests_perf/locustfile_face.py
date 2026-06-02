"""PERF-004 — tải đồng thời nhận diện + đăng ký khuôn mặt (backend, fake remote).

Cần: fake_face_api chạy + runserver với FACE_API_BASE_URL trỏ fake +
tests_perf/perf_users.json (map username→user_id) đã tạo.

Chạy nhận diện 50 đồng thời:
  locust -f tests_perf/locustfile_face.py --headless -u 50 -r 10 -t 30s \
         --host http://127.0.0.1:8000 RecognizeUser --only-summary
Chạy đăng ký 30 đồng thời:
  locust -f tests_perf/locustfile_face.py --headless -u 30 -r 10 -t 30s \
         --host http://127.0.0.1:8000 EnrollUser --only-summary
"""
import itertools
import json
import os
import re

from locust import HttpUser, between, task

_DIR = os.path.dirname(__file__)
with open(os.path.join(_DIR, 'perf_users.json'), encoding='utf-8') as f:
    USER_IDS = json.load(f)            # {"perf001": 12, ...}
USERNAMES = sorted(USER_IDS.keys())
_counter = itertools.count()
PASSWORD = 'PerfPass123!'


def _login(client, username):
    r = client.get('/login/')
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
    token = m.group(1) if m else ''
    client.post('/login/', {
        'username': username, 'password': PASSWORD,
        'csrfmiddlewaretoken': token,
    }, headers={'Referer': f'{client.base_url}/login/'})


def _csrf_headers(client):
    return {
        'X-CSRFToken': client.cookies.get('csrftoken', ''),
        'Referer': f'{client.base_url}/',
    }


class RecognizeUser(HttpUser):
    """Chấm công FaceID đồng thời — POST /attendance/check/."""
    wait_time = between(0.2, 0.6)

    def on_start(self):
        self.username = USERNAMES[next(_counter) % len(USERNAMES)]
        self.uid = USER_IDS[self.username]
        _login(self.client, self.username)

    @task
    def check(self):
        files = {'image': ('p.jpg', f'UID:{self.uid}'.encode(), 'image/jpeg')}
        self.client.post('/attendance/check/', files=files,
                         headers=_csrf_headers(self.client), name='/attendance/check/')


class EnrollUser(HttpUser):
    """Đăng ký khuôn mặt đồng thời — POST /attendance/upload-image/."""
    wait_time = between(0.5, 1.0)

    def on_start(self):
        self.username = USERNAMES[next(_counter) % len(USERNAMES)]
        self.uid = USER_IDS[self.username]
        _login(self.client, self.username)

    @task
    def enroll(self):
        files = {'image': ('f.jpg', f'UID:{self.uid}-face'.encode(), 'image/jpeg')}
        self.client.post('/attendance/upload-image/', files=files,
                         headers=_csrf_headers(self.client), name='/attendance/upload-image/')
