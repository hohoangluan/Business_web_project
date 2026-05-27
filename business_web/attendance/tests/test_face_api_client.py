"""Unit tests for face_api_client — mocks requests entirely."""
from unittest.mock import patch, MagicMock

import requests
from django.test import SimpleTestCase, override_settings

from attendance.services import face_api_client as client


@override_settings(FACE_API_URL='http://test:9999', FACE_API_TIMEOUT_SEC=5)
class HealthCheckTests(SimpleTestCase):
    @patch('attendance.services.face_api_client.requests.get')
    def test_health_check_ok(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'status': 'ok', 'engine': 'FAISS'}
        )
        self.assertTrue(client.health_check())

    @patch('attendance.services.face_api_client.requests.get')
    def test_health_check_non_ok_status(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'status': 'down'}
        )
        self.assertFalse(client.health_check())

    @patch('attendance.services.face_api_client.requests.get',
           side_effect=requests.ConnectionError())
    def test_health_check_unreachable_returns_false(self, mock_get):
        self.assertFalse(client.health_check())


@override_settings(FACE_API_URL='http://test:9999', FACE_API_TIMEOUT_SEC=5)
class RegisterFaceRemoteTests(SimpleTestCase):
    @patch('attendance.services.face_api_client.requests.post')
    def test_register_success_returns_dict(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'status': 'success', 'message': 'Saved'},
        )
        out = client.register_face_remote('42', b'\xff\xd8\xff bytes', slot_id=1)
        self.assertEqual(out['status'], 'success')
        # Verify slot_id was sent as multipart field
        call_kwargs = mock_post.call_args.kwargs
        self.assertIn('data', call_kwargs)
        self.assertEqual(call_kwargs['data']['employee_id'], '42')
        self.assertEqual(call_kwargs['data']['slot_id'], 1)

    @patch('attendance.services.face_api_client.requests.post')
    def test_register_no_face_detected_raises(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=400, text='No face detected in image',
            json=lambda: {'detail': 'No face detected in image'},
        )
        with self.assertRaises(client.FaceApiError) as ctx:
            client.register_face_remote('42', b'bytes', slot_id=1)
        self.assertEqual(ctx.exception.code, 'no_face')

    @patch('attendance.services.face_api_client.requests.post',
           side_effect=requests.ConnectionError())
    def test_register_unreachable_raises(self, mock_post):
        with self.assertRaises(client.FaceApiError) as ctx:
            client.register_face_remote('42', b'bytes', slot_id=1)
        self.assertEqual(ctx.exception.code, 'unreachable')

    @patch('attendance.services.face_api_client.requests.post',
           side_effect=requests.Timeout())
    def test_register_timeout_raises(self, mock_post):
        with self.assertRaises(client.FaceApiError) as ctx:
            client.register_face_remote('42', b'bytes', slot_id=1)
        self.assertEqual(ctx.exception.code, 'timeout')

    @patch('attendance.services.face_api_client.requests.post')
    def test_register_bad_response_other_4xx(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=500, text='boom', json=lambda: {'detail': 'boom'}
        )
        with self.assertRaises(client.FaceApiError) as ctx:
            client.register_face_remote('42', b'bytes', slot_id=1)
        self.assertEqual(ctx.exception.code, 'bad_response')

    @patch('attendance.services.face_api_client.requests.post')
    def test_register_json_decode_failure_bad_response(self, mock_post):
        bad = MagicMock(status_code=200, text='not json')
        bad.json.side_effect = ValueError('no json')
        mock_post.return_value = bad
        with self.assertRaises(client.FaceApiError) as ctx:
            client.register_face_remote('42', b'bytes', slot_id=1)
        self.assertEqual(ctx.exception.code, 'bad_response')


@override_settings(FACE_API_URL='http://test:9999', FACE_API_TIMEOUT_SEC=5)
class RecognizeFaceRemoteTests(SimpleTestCase):
    @patch('attendance.services.face_api_client.requests.post')
    def test_recognize_success_returns_dict(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'status': 'success', 'employee_id': '42',
                          'confidence': '95.4%', 'match_slot': 1},
        )
        out = client.recognize_face_remote(b'bytes')
        self.assertEqual(out['employee_id'], '42')

    @patch('attendance.services.face_api_client.requests.post')
    def test_recognize_fail_status_does_not_raise(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'status': 'fail', 'message': 'Unknown person'},
        )
        out = client.recognize_face_remote(b'bytes')
        self.assertEqual(out['status'], 'fail')

    @patch('attendance.services.face_api_client.requests.post',
           side_effect=requests.Timeout())
    def test_recognize_timeout_raises(self, mock_post):
        with self.assertRaises(client.FaceApiError) as ctx:
            client.recognize_face_remote(b'bytes')
        self.assertEqual(ctx.exception.code, 'timeout')
