from django import forms
from django.db import models
from django.contrib.auth.models import User
from accounts.models import Role
from accounts.services import get_user_role_name
from common.file_validation import EVIDENCE_MIME, validate_upload
from reports_interactions.models import Report
from reports_interactions.models.ticket_model import Ticket

class ReportForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Người nhận báo cáo",
        empty_label="-- Chọn Cấp quản lý nhận báo cáo --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Report
        fields = ['recipient', 'title', 'content', 'file_attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề báo cáo...',
                'autocomplete': 'off'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập nội dung báo cáo tự do ở đây...',
                'rows': 6,
                'style': 'resize: none;'
            }),
            'file_attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }
        labels = {
            'title': 'Tiêu đề báo cáo',
            'content': 'Nội dung báo cáo',
            'file_attachment': 'Tài liệu / File đính kèm (nếu có)',
        }

    def clean_file_attachment(self):
        # Đính kèm tùy chọn → validator dùng chung (5 MB + PDF/JPG/PNG).
        return validate_upload(self.cleaned_data.get('file_attachment'))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 1. Lọc danh sách người nhận chỉ gồm các tài khoản có vai trò Quản lý/Leader/HR/Admin hoặc Superuser
        eligible_users = User.objects.all()
        if user:
            eligible_users = eligible_users.exclude(id=user.id)
        
        # Chỉ lấy những user có UserProfile và có role thuộc admin, hr, manager, leader, hoặc là superuser
        eligible_users = eligible_users.filter(
            models.Q(profile__role__name__in=[Role.ADMIN, Role.HR, Role.MANAGER, Role.LEADER]) |
            models.Q(is_superuser=True)
        ).distinct()

        self.fields['recipient'].queryset = eligible_users

        # 2. Xác định người nhận mặc định theo sơ đồ cấp bậc phân quyền
        if user and not self.instance.pk:
            default_recipient = self.get_default_recipient(user)
            if default_recipient:
                self.fields['recipient'].initial = default_recipient

    def get_default_recipient(self, user):
        """
        Xác định người nhận mặc định:
        - Employee: gửi cho Leader, nếu không có Leader thì gửi cho Manager.
        - Leader: gửi cho Manager.
        - Manager: gửi cho Manager của Manager (trường manager_user của chính họ).
        - HR: gửi cho Manager.
        """
        from employee_profiles.models import EmployeeWorkInfo
        try:
            work_info = user.work_info
        except EmployeeWorkInfo.DoesNotExist:
            return None

        role = get_user_role_name(user)
        if role == Role.EMPLOYEE:
            return work_info.leader_user or work_info.manager_user
        elif role == Role.LEADER:
            return work_info.manager_user
        elif role == Role.MANAGER:
            return work_info.manager_user
        elif role == Role.HR:
            return work_info.manager_user
        return work_info.manager_user or work_info.leader_user

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['ticket_type', 'priority', 'title', 'content', 'evidence_file']
        widgets = {
            'ticket_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề ticket...',
                'autocomplete': 'off'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Mô tả chi tiết vấn đề bạn đang gặp phải...',
                'rows': 5,
                'style': 'resize: none;'
            }),
            'evidence_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }
        labels = {
            'ticket_type': 'Loại yêu cầu',
            'priority': 'Mức độ ưu tiên',
            'title': 'Tiêu đề ticket',
            'content': 'Nội dung chi tiết',
            'evidence_file': 'File minh chứng đính kèm (nếu có)',
        }

    def clean_evidence_file(self):
        # Minh chứng tùy chọn → ảnh (JPG/PNG/GIF/WEBP) hoặc PDF, ≤5 MB.
        return validate_upload(
            self.cleaned_data.get('evidence_file'),
            allowed_mime=EVIDENCE_MIME,
            mime_message='Sai định dạng. Chấp nhận: ảnh hoặc PDF.',
        )
