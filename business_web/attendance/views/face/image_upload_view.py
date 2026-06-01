"""View xử lý upload ảnh và lưu base64 vào database."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

from attendance.services.face.face_service import (
    get_employee_face,
    delete_employee_face,
)
from attendance.services.face.face_change_service import submit_face_change
from attendance.services.face.face_api_client import FaceApiError


def _client_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
@require_POST
def upload_image_base64_view(request):
    """
    API nhận ảnh từ frontend, chuyển sang base64 và lưu vào database.

    Request:
        - Method: POST
        - Content-Type: multipart/form-data
        - Body: field "image" chứa file ảnh

    Response (200):
        {
            "success": true,
            "message": "Lưu ảnh thành công.",
            "data": {
                "base64": "<chuỗi base64>",
                "content_type": "image/jpeg",
                "updated_at": "2025-05-21T12:30:00Z"
            }
        }
    """
    image_file = request.FILES.get("image")

    if not image_file:
        return JsonResponse(
            {"success": False, "error": "Không tìm thấy file ảnh. Vui lòng gửi file với field 'image'."},
            status=400,
        )

    # Kiểm tra MIME type có phải là ảnh không
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"]
    if image_file.content_type not in allowed_types:
        return JsonResponse(
            {
                "success": False,
                "error": f"Loại file không hợp lệ: {image_file.content_type}. "
                         f"Chỉ chấp nhận: {', '.join(allowed_types)}.",
            },
            status=400,
        )

    try:
        outcome, obj = submit_face_change(
            owner=request.user,
            submitted_by=request.user,
            image_file=image_file,
            ip_address=_client_ip(request),
        )
    except FaceApiError as exc:
        status = 400 if exc.code == 'no_face' else 502
        return JsonResponse(
            {"success": False,
             "error": exc.message or exc.code,
             "code": exc.code},
            status=status,
        )
    except ValueError as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=400,
        )

    # Self-service → chờ HR duyệt; chưa thay khuôn mặt đang dùng để nhận diện.
    if outcome == 'pending':
        return JsonResponse({
            "success": True,
            "pending": True,
            "message": "Đã gửi yêu cầu cập nhật khuôn mặt. Chờ HR duyệt mới có hiệu lực.",
        })

    return JsonResponse({
        "success": True,
        "pending": False,
        "message": "Lưu ảnh thành công.",
        "data": {
            "base64": obj.face_base64,
            "content_type": obj.content_type,
            "updated_at": obj.updated_at.isoformat(),
        },
    })


@login_required
@require_http_methods(["GET"])
def get_image_base64_view(request):
    """
    API lấy ảnh base64 của nhân viên đang đăng nhập.

    Response (200):
        {
            "success": true,
            "data": {
                "base64": "<chuỗi base64>",
                "content_type": "image/jpeg",
                "updated_at": "2025-05-21T12:30:00Z"
            }
        }
    """
    face_data = get_employee_face(user=request.user)

    if face_data is None:
        return JsonResponse(
            {"success": False, "error": "Nhân viên chưa có ảnh khuôn mặt."},
            status=404,
        )

    return JsonResponse({
        "success": True,
        "data": {
            "base64": face_data['base64'],
            "content_type": face_data['content_type'],
            "updated_at": face_data['updated_at'].isoformat(),
        },
    })
