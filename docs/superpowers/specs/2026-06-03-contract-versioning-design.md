# Spec: Versioning hợp đồng + trang lịch sử HĐ

**Ngày:** 2026-06-03
**Trạng thái:** Đã duyệt (chờ review spec)

## 1. Bối cảnh & Vấn đề

`ContractInfo` được thiết kế cho lịch sử (`is_active`, docstring "có lưu lịch sử", quan hệ `1 User → N ContractInfo`), nhưng luồng sửa hiện tại **ghi đè tại chỗ**:

- [edit_work_info_view](../../../business_web/employee_profiles/views/profile_views.py) → `save_contract_info_from_data` → `ensure_contract_info` (lấy HĐ active) → mutate field → `.save()` = UPDATE cùng row.
- Dữ liệu HĐ cũ bị mất, không truy vết được điều chỉnh.

## 2. Mục tiêu

1. Mỗi lần **điều chỉnh HĐ** = tạo `ContractInfo` mới: copy toàn bộ field từ HĐ active hiện tại, ghi đè các field được sửa, đặt làm active; HĐ cũ giữ lại với `is_active=False`.
2. Trang **lịch sử HĐ** riêng cho phép xem mọi phiên bản (active + archived) dạng snapshot đầy đủ.
3. Một đường ghi HĐ duy nhất (qua nút "Điều chỉnh HĐ"); gỡ field HĐ khỏi form edit_work_info chung.

Phi mục tiêu (YAGNI): không làm diff/highlight thay đổi; không cho sửa/xóa HĐ đã archive; không versioning cho work_info/personal_info.

## 3. Quyết định thiết kế (đã chốt với user)

| Vấn đề | Quyết định |
|--------|-----------|
| Trigger tạo phiên bản | Nút/form riêng "Điều chỉnh HĐ" (tách khỏi edit_work_info) |
| Giao diện lịch sử | Trang riêng `/contracts/history/<user_id>/` |
| Quyền xem lịch sử | HR/Admin xem tất cả; nhân viên xem của chính mình (read-only) |
| Cách hiển thị | Snapshot đầy đủ mỗi phiên bản |
| Field HĐ trong edit_work_info | **Gỡ bỏ** — HĐ chỉ sửa qua trang điều chỉnh riêng |

## 4. Kiến trúc

### 4.1 Model — `contracts/models/contract_info_model.py`

Thêm field timestamp để sắp xếp/timeline:

```python
created_at = models.DateTimeField(
    auto_now_add=True,
    help_text="Thời điểm tạo bản HĐ này (dùng cho lịch sử).",
)
```

- Migration `0003_contractinfo_created_at`. Row cũ sẽ nhận giá trị thời điểm chạy migration (auto_now_add default).
- `ensure_contract_info` đã dùng `filter(is_active=True).order_by('-id')` → vẫn trả bản active mới nhất, không đổi.

### 4.2 Service — `contracts/services/__init__.py` (hoặc module mới `versioning_service.py`)

```python
def adjust_contract(user, data):
    """Tạo phiên bản HĐ mới từ HĐ active hiện tại + field sửa. Trả HĐ mới."""
    # transaction.atomic:
    #   old = ensure_contract_info(user)            # HĐ active hiện tại
    #   carry = snapshot field từ old (mọi field HĐ)
    #   carry.update(data)                          # ghi đè field sửa
    #   old.is_active = False; old.save(update_fields=['is_active'])
    #   return ContractInfo.objects.create(user=user, is_active=True, **carry)

def get_contract_history(user):
    """Mọi phiên bản HĐ của user, mới nhất trước."""
    return user.contracts.order_by('-created_at', '-id')
```

- `adjust_contract` bọc `transaction.atomic()` để archive + create là nguyên tử.
- Danh sách field copy: `contract_number, contract_type, contract_signed_date, contract_start_date, contract_end_date, contract_annual_leave_days, contract_standard_shift, shift_start_time, shift_end_time, contract_attachment_reference`.

### 4.3 Form — `contracts/forms.py`

`ContractAdjustForm(forms.Form)` chứa **chỉ field HĐ** (di chuyển từ `EmployeeProfileForm`):
`contract_number, contract_type, contract_signed_date, contract_start_date, contract_end_date, contract_annual_leave_days, contract_standard_shift, shift_start_time, shift_end_time, contract_attachment_reference`.

`clean()` tái dùng logic ngày hiện có trong `EmployeeProfileForm.clean()`:
- Regex `DD/MM/YYYY` cho 3 field ngày.
- `validate_contract_date_order(...)` (đã tồn tại trong `contracts.services`).

### 4.4 Views — `contracts/views/__init__.py` (re-export từ module mới `contract_history_view.py`)

```python
@login_required
@deny_admin
@user_passes_test(can_manage_work_info)   # HR/Admin
def hr_adjust_contract_view(request, user_id):
    # GET: ContractAdjustForm prefill từ ensure_contract_info(target)
    # POST hợp lệ: adjust_contract(target, form.cleaned_data) → message → redirect contract_history

@login_required
def contract_history_view(request, user_id):
    # Quyền: is_hr_user/can_manage_work_info(request.user) HOẶC request.user.id == user_id
    #   (admin bị chặn như các view hồ sơ khác)
    # context: target_user + get_contract_history(target_user)
```

Permission "own-or-HR" kiểm tra trong thân view; trả 403/redirect nếu không đủ.

### 4.5 URLs — `contracts/urls.py`

```python
path('contract/hr/adjust/<int:user_id>/', hr_adjust_contract_view, name='hr_adjust_contract'),
path('contract/history/<int:user_id>/',   contract_history_view,   name='contract_history'),
```

### 4.6 Templates (UI mới)

- `contracts/hr_adjust_contract.html` — form điều chỉnh HĐ (giống layout phần HĐ cũ trong edit_work_info), nút Lưu / Hủy.
- `contracts/contract_history.html` — bảng/timeline: mỗi phiên bản 1 thẻ snapshot đầy đủ field, badge **"Đang hiệu lực"** (is_active) / **"Đã thay thế"**, kèm `created_at`. Sắp mới nhất trên cùng.
- Cập nhật `employee_profiles/hr_view_profile.html`: nút **"Điều chỉnh HĐ"** (→ `hr_adjust_contract`) + **"Xem lịch sử HĐ"** (→ `contract_history`) trong khu vực hợp đồng.
- Cập nhật `contracts/contract.html` (nhân viên): nút **"Xem lịch sử HĐ"** (→ `contract_history` với user.id của chính mình).

### 4.7 Gỡ field HĐ khỏi edit_work_info

- `employee_profiles/forms.py`: xóa các field HĐ khỏi `EmployeeProfileForm` + phần validate ngày HĐ trong `clean()` (đã chuyển sang `ContractAdjustForm`).
- `employee_profiles/views/profile_views.py`: bỏ lời gọi `save_contract_info_from_data(...)` trong `edit_work_info_view`; bỏ field HĐ khỏi `initial` dict.
- `employee_profiles/templates/employee_profiles/edit_work_info.html`: gỡ section field HĐ; thay bằng link sang trang điều chỉnh HĐ.
- `save_contract_info_from_data` vẫn dùng bởi `hr_create_profile_view` (tạo HĐ đầu tiên) → **giữ lại**, không xóa.

## 5. Luồng dữ liệu

```
HR bấm "Điều chỉnh HĐ" (hr_view_profile)
  → GET hr_adjust_contract: form prefill HĐ active
  → POST: form.is_valid()
      → adjust_contract(target, cleaned_data)
          old.is_active=False  +  ContractInfo.create(active, carry+edits)
      → redirect contract_history (thấy bản mới trên cùng, bản cũ "Đã thay thế")

Nhân viên / HR bấm "Xem lịch sử HĐ"
  → contract_history: get_contract_history → render snapshot list
```

## 6. Xử lý lỗi & biên

- Ngày sai định dạng / sai thứ tự → form error, không tạo phiên bản.
- User chưa có HĐ active → `ensure_contract_info` tạo 1 bản trống active trước, adjust hoạt động bình thường.
- Nhân viên truy cập history của người khác → chặn (403/redirect).
- Admin truy cập (deny_admin pattern) → chặn như các view hồ sơ khác.
- Concurrency: archive+create trong `transaction.atomic()`.

## 7. Kế hoạch test (`contracts/tests/test_contract_versioning.py`)

1. `adjust_contract` tạo +1 row; HĐ cũ `is_active=False`, HĐ mới `is_active=True`.
2. Field không sửa **carry-forward** đúng; field sửa được áp giá trị mới.
3. `ensure_contract_info` sau adjust trả bản mới.
4. `get_contract_history` trả mọi phiên bản, mới nhất trước.
5. Quyền: chủ sở hữu xem được history mình; nhân viên khác bị chặn; HR xem được mọi người.
6. Form: ngày sai định dạng / sai thứ tự → invalid, không tạo phiên bản.
7. `edit_work_info_view` không còn tạo/đổi HĐ (lưu hồ sơ không sinh phiên bản HĐ mới).

## 8. File chạm tới

**Mới:** `contracts/views/contract_history_view.py`, `contracts/templates/contracts/hr_adjust_contract.html`, `contracts/templates/contracts/contract_history.html`, `contracts/tests/test_contract_versioning.py`, migration `0003`.

**Sửa:** `contracts/models/contract_info_model.py`, `contracts/services/__init__.py`, `contracts/forms.py`, `contracts/views/__init__.py`, `contracts/urls.py`, `employee_profiles/forms.py`, `employee_profiles/views/profile_views.py`, `employee_profiles/templates/employee_profiles/edit_work_info.html`, `employee_profiles/templates/employee_profiles/hr_view_profile.html`, `contracts/templates/contracts/contract.html`.
