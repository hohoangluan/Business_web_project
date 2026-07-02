"""Company-level configuration editable by system Admins."""

from django.db import models


DEFAULT_WORKPLACES = "\n".join([
    "Văn phòng Hà Nội",
    "Văn phòng TP.HCM",
    "Văn phòng Đà Nẵng",
    "Remote",
    "Hybrid",
])

DEFAULT_CONTRACT_TYPES = "\n".join([
    "Thử việc",
    "Xác định thời hạn",
    "Không xác định thời hạn",
    "Thời vụ",
])

DEFAULT_DEPARTMENTS = "\n".join([
    "Nhân sự",
    "Kinh doanh",
    "Kế toán",
    "Công nghệ thông tin",
    "Marketing",
    "Vận hành",
])

DEFAULT_POSITIONS = "\n".join([
    "Nhân viên",
    "Chuyên viên",
    "Trưởng nhóm",
    "Quản lý",
    "Trưởng phòng",
])

DEFAULT_REWARD_POLICY = "\n".join([
    "Thưởng theo thành tích hoàn thành vượt chỉ tiêu.",
    "Thưởng đột xuất cho đóng góp nổi bật được quản lý/HR xác nhận.",
    "Mức thưởng cụ thể do HR duyệt theo ngân sách và minh chứng kèm theo.",
])

DEFAULT_PENALTY_POLICY = "\n".join([
    "Xử phạt vi phạm nội quy sau khi có minh chứng hoặc biên bản xác nhận.",
    "Mức phạt căn cứ theo mức độ ảnh hưởng và quy định nội bộ hiện hành.",
    "Nhân viên được thông báo lý do trước khi phiếu xử phạt được áp dụng.",
])


def _lines(value):
    """Return unique non-empty lines while preserving the configured order."""

    seen = set()
    result = []
    for raw in (value or "").splitlines():
        item = raw.strip()
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result


class CompanyConfiguration(models.Model):
    """Singleton configuration for company-controlled HR catalog values."""

    workplaces = models.TextField(
        default=DEFAULT_WORKPLACES,
        help_text="Danh sách nơi làm việc, mỗi dòng một giá trị.",
    )
    contract_types = models.TextField(
        default=DEFAULT_CONTRACT_TYPES,
        help_text="Danh sách loại hợp đồng lao động, mỗi dòng một giá trị.",
    )
    reward_policy = models.TextField(
        default=DEFAULT_REWARD_POLICY,
        help_text="Cơ chế khen thưởng nội bộ.",
    )
    penalty_policy = models.TextField(
        default=DEFAULT_PENALTY_POLICY,
        help_text="Cơ chế xử phạt nội bộ.",
    )
    departments = models.TextField(
        default=DEFAULT_DEPARTMENTS,
        help_text="Danh sách phòng ban, mỗi dòng một giá trị.",
    )
    positions = models.TextField(
        default=DEFAULT_POSITIONS,
        help_text="Danh sách chức vụ, mỗi dòng một giá trị.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        """Return the single configuration row, creating defaults if needed."""

        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def list_for(self, field_name):
        """Return the normalized list configured for a catalog field."""

        return _lines(getattr(self, field_name, ""))

    def choices_for(self, field_name, empty_label):
        """Return Django choices from a configured newline list."""

        return [("", empty_label)] + [(item, item) for item in self.list_for(field_name)]

    def __str__(self):
        return "Cấu hình công ty"

    class Meta:
        verbose_name = "Cấu hình công ty"
        verbose_name_plural = "Cấu hình công ty"
