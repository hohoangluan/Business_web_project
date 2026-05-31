import base64
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from PIL import Image


def image_to_base64(image) -> str:
    """
    Nhận input là một ảnh và trả về chuỗi base64 của ảnh đó.

    Args:
        image: Có thể là một trong các loại sau:
            - Django UploadedFile (InMemoryUploadedFile hoặc TemporaryUploadedFile)
            - PIL Image object
            - Đường dẫn file (str) trên hệ thống
            - Bytes của ảnh

    Returns:
        str: Chuỗi base64 của ảnh (không bao gồm prefix data URI).

    Raises:
        ValueError: Nếu input không hợp lệ hoặc không đọc được.
    """
    try:
        if isinstance(image, (InMemoryUploadedFile, TemporaryUploadedFile)):
            # Django uploaded file
            image.seek(0)
            image_data = image.read()
            image.seek(0)  # Reset lại vị trí để có thể đọc lại nếu cần

        elif isinstance(image, Image.Image):
            # PIL Image object
            buffer = BytesIO()
            img_format = image.format or "PNG"
            image.save(buffer, format=img_format)
            image_data = buffer.getvalue()

        elif isinstance(image, str):
            # Đường dẫn file
            with open(image, "rb") as f:
                image_data = f.read()

        elif isinstance(image, bytes):
            # Raw bytes
            image_data = image

        else:
            raise ValueError(
                f"Loại input không được hỗ trợ: {type(image)}. "
                "Chấp nhận: Django UploadedFile, PIL Image, đường dẫn file (str), hoặc bytes."
            )

        return base64.b64encode(image_data).decode("utf-8")

    except (OSError, IOError) as e:
        raise ValueError(f"Không thể đọc ảnh: {e}") from e
