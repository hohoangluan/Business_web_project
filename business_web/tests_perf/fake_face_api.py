"""Fake Remote Face API — cô lập backend cho PERF-004.

Trả lời tức thì (không AI thật) để đo riêng tải backend Django/DB.
  - GET  /health     -> {"status":"ok"}
  - POST /register    -> {"status":"success"}
  - POST /recognize   -> đọc 'UID:<id>' trong body multipart, echo employee_id=id
                          (locust nhúng UID của user vào ảnh) → verify 1:1 pass.
Chạy:  python tests_perf/fake_face_api.py 9100
"""
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_UID = re.compile(rb'UID:(\d+)')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/health'):
            self._send(200, {'status': 'ok'})
        else:
            self._send(404, {'detail': 'not found'})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0) or 0)
        body = self.rfile.read(length) if length else b''
        if self.path.startswith('/register'):
            self._send(200, {'status': 'success'})
        elif self.path.startswith('/recognize'):
            m = _UID.search(body)
            if m:
                self._send(200, {
                    'status': 'success',
                    'employee_id': m.group(1).decode(),
                    'confidence': 99.0,
                })
            else:
                self._send(200, {'status': 'fail', 'message': 'no match'})
        else:
            self._send(404, {'detail': 'not found'})


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9100
    print(f'fake face api on :{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
