"""URL config cho contracts app."""
from django.urls import path
from contracts.views import (
    contract_view,
    hr_expiring_contracts_view,
    hr_send_reminder_view,
    hr_send_all_reminders_view,
    hr_adjust_contract_view,
    contract_history_view,
)

urlpatterns = [
    # Nhân viên xem hợp đồng cá nhân
    path('contract/', contract_view, name='contract'),

    # HR xem danh sách hợp đồng sắp hết hạn
    path('contract/hr/expiring/', hr_expiring_contracts_view, name='hr_expiring_contracts'),

    # HR gửi nhắc nhở 1 nhân viên cụ thể (POST only)
    path('contract/hr/send-reminder/<int:user_id>/', hr_send_reminder_view, name='hr_send_reminder'),

    # HR gửi nhắc nhở tất cả (POST only)
    path('contract/hr/send-all-reminders/', hr_send_all_reminders_view, name='hr_send_all_reminders'),

    # HR điều chỉnh HĐ (tạo phiên bản mới)
    path('contract/hr/adjust/<int:user_id>/', hr_adjust_contract_view, name='hr_adjust_contract'),

    # Xem lịch sử HĐ (HR mọi người / nhân viên của mình)
    path('contract/history/<int:user_id>/', contract_history_view, name='contract_history'),
]
