# Danh mục Quy định & Biểu mẫu — Business Web Project

Tài liệu liệt kê toàn bộ **quy định nghiệp vụ (QĐ)** và **biểu mẫu (BM)** hiện có trong dự án,
trích xuất trực tiếp từ mã nguồn (`models/`, `forms/`, `services/`, `settings.py`).

## Quy ước đặt tên

- **Quy định:** `QĐ_<Tên chức năng viết tắt>_<STT>`
- **Biểu mẫu:** `BM_<Chứa thông tin gì>_<STT>`

STT chỉ dùng khi cùng nhóm có nhiều mục trùng tên.

### Bảng viết tắt chức năng

| Viết tắt | Chức năng | App |
|----------|-----------|-----|
| TK | Tài khoản | `accounts` |
| DN | Đăng nhập | `accounts` |
| QMK | Quên / đặt lại mật khẩu | `accounts` |
| PQ | Phân quyền (role + permission) | `accounts` |
| CC | Chấm công | `attendance` |
| KM | Khuôn mặt (nhận diện) | `attendance` |
| DCCC | Điều chỉnh chấm công | `attendance` |
| NP | Nghỉ phép | `leaves` |
| TC | Tăng ca (overtime) | `overtime` |
| HD | Hợp đồng lao động | `contracts` |
| DG | Đánh giá nhân viên | `performance` |
| BC | Báo cáo | `reports_interactions` |
| HT | Ticket hỗ trợ / khiếu nại | `reports_interactions` |
| KTXP | Khen thưởng / Xử phạt | `rewards_discipline` |
| HS | Hồ sơ nhân viên | `employee_profiles` |

---

## 1. QUY ĐỊNH NGHIỆP VỤ (QĐ)

### 1.1. Tài khoản & Xác thực

| Mã | Tên quy định | Nội dung | Nguồn |
|----|--------------|----------|-------|
| **QĐ_TK_01** | Đăng ký tài khoản | Mã nhân viên (`employee_id`) **duy nhất**, không trống; username = mã NV viết thường, bỏ khoảng trắng. Mật khẩu phải qua `validate_password` của Django. Email (tùy chọn) phải **duy nhất** nếu nhập. | `accounts/forms/auth/register_form.py` |
| **QĐ_DN_01** | Đăng nhập | Xác thực bằng username (mã NV) + mật khẩu, dùng `AuthenticationForm` của Django. | `accounts/forms/auth/login_form.py` |
| **QĐ_QMK_01** | Khôi phục mật khẩu bằng OTP | OTP **6 chữ số**, hiệu lực **120 giây (2 phút)** kể từ khi tạo; xóa ngay sau khi xác thực thành công hoặc hết hạn. | `accounts/models/otp_code_model.py` |
| **QĐ_QMK_02** | Đặt lại mật khẩu | Mật khẩu mới **tối thiểu 8 ký tự**; hai ô mật khẩu phải khớp nhau. | `accounts/forms/auth/reset_password_form.py` |
| **QĐ_PQ_01** | Phân quyền theo vai trò | 5 vai trò hệ thống: `admin`, `hr`, `manager`, `leader`, `employee`. Mỗi user gắn 1 role quyết định giao diện + quyền truy cập. | `accounts/models/role_model.py` |
| **QĐ_PQ_02** | Quyền tùy chỉnh | Ngoài role, gán thêm `CustomPermission` (theo `codename`) tách riêng khỏi vai trò. | `accounts/models/permission_model.py`, `account_model.py` |

### 1.2. Chấm công & Nhận diện khuôn mặt

| Mã | Tên quy định | Nội dung | Nguồn |
|----|--------------|----------|-------|
| **QĐ_CC_01** | Phân loại bản ghi chấm công | Ca chuẩn **08:30 – 17:30**. Trễ (`late`) nếu vào sau giờ vào + **5 phút** ân hạn; về sớm (`early_leave`) nếu ra trước giờ tan ca; còn lại `on_time`. NV có tăng ca approved thì mốc về sớm tính theo giờ OT. | `settings.py` (WORK_START/END_TIME, WORK_LATE_GRACE_MIN), `attendance/services/record/attendance_logging_service.py` |
| **QĐ_CC_02** | Một bản ghi / ngày | Mỗi nhân viên chỉ có **1 bản ghi chấm công cho mỗi ngày** (`unique_together = user + record_date`). | `attendance/models/attendance_record_model.py` |
| **QĐ_CC_03** | Đóng bản ghi treo | Bản ghi có giờ vào nhưng thiếu giờ ra, ngày < cutoff (mặc định hôm nay) sẽ bị đóng với trạng thái `no_checkout` (idempotent). | `attendance/management/commands/close_open_attendance.py` |
| **QĐ_KM_01** | Khóa nhận diện khuôn mặt | Sai nhận diện **3 lần** (`FACE_LOCKOUT_MAX_FAILS`) → khóa **300 giây** (`FACE_LOCKOUT_DURATION_SEC`). Vector & so khớp do service từ xa xử lý; ảnh lưu local chỉ để preview. | `settings.py`, `attendance/services/face/face_lockout_service.py` |
| **QĐ_KM_02** | Đổi khuôn mặt phải HR duyệt | Cập nhật khuôn mặt **không hiệu lực ngay**, lưu trạng thái `pending` chờ HR duyệt; lưu SHA-256 + IP, gắn cờ nghi vấn `is_cross_user` khi người upload khác chủ khuôn mặt (chống đổi mặt hộ). | `attendance/models/face_change_request_model.py` |
| **QĐ_DCCC_01** | Yêu cầu điều chỉnh chấm công | **Bắt buộc** minh chứng (ảnh JPG/PNG/GIF/WEBP hoặc PDF, **≤ 5MB**); phải khai ít nhất 1 trong 2 giờ (vào / ra); lý do thuộc {quên chấm ra, lỗi kỹ thuật, công tác, khác}; HR duyệt/từ chối (`pending → approved/rejected`). | `attendance/forms/adjustment/attendance_adjustment_form.py`, `attendance_adjustment_request_model.py` |

### 1.3. Nghỉ phép & Tăng ca

| Mã | Tên quy định | Nội dung | Nguồn |
|----|--------------|----------|-------|
| **QĐ_NP_01** | Quy trình duyệt nghỉ phép 2 bước | Bước 1: Leader/Manager duyệt (`leader_approved`); Bước 2: HR duyệt cuối (`approved`). **Ngoại lệ:** người tạo là HR chỉ cần bước 1. Loại nghỉ: phép năm/ốm/việc riêng/thai sản/công tác/khác. Minh chứng PDF/JPG/PNG ≤ 5MB. | `leaves/models/leave_request_model.py` |
| **QĐ_TC_01** | Quy trình duyệt tăng ca 2 bước | Tương tự nghỉ phép: Leader/Manager → HR; HR chỉ cần bước 1. Ghi nhận ngày, giờ bắt đầu/kết thúc, số giờ, lý do, minh chứng ≤ 5MB. | `overtime/models/overtime_request_model.py` |

### 1.4. Hợp đồng

| Mã | Tên quy định | Nội dung | Nguồn |
|----|--------------|----------|-------|
| **QĐ_HD_01** | Quản lý hợp đồng lao động | 1 User → N hợp đồng (có lịch sử), nhưng **chỉ 1 hợp đồng active** tại một thời điểm. Lưu giờ ca chuẩn (dùng cho QĐ_CC_01). | `contracts/models/contract_info_model.py` |
| **QĐ_HD_02** | Nhắc gia hạn hợp đồng | Cảnh báo khi sắp hết hạn ở **2 ngưỡng: 30 ngày và 7 ngày**; ≤ 7 ngày gắn nhãn **[KHẨN]** trong email nhắc. | `contracts/services/renewal_service.py`, `email_service.py` |

### 1.5. Đánh giá, Báo cáo, Ticket, Khen thưởng/Xử phạt

| Mã | Tên quy định | Nội dung | Nguồn |
|----|--------------|----------|-------|
| **QĐ_DG_01** | Đánh giá nhân viên | Manager/Leader chấm điểm thang **100**, tự suy xếp loại: **A ≥ 90, B ≥ 75, C ≥ 60, còn lại D**. Trạng thái: `draft → submitted → acknowledged` (HR xác nhận). Loại đánh giá do HR/Admin cấu hình. | `performance/models/evaluation_model.py` |
| **QĐ_BC_01** | Báo cáo theo phân cấp | NV gửi báo cáo lên quản lý theo sơ đồ phân cấp. Khi quản lý đã tiếp nhận (`acknowledged`), người gửi **không được sửa/xóa**. Trạng thái: `submitted / needs_update / acknowledged`. | `reports_interactions/models/report_model.py` |
| **QĐ_HT_01** | Ticket hỗ trợ / khiếu nại | Loại: hỗ trợ / khiếu nại; mức ưu tiên: thấp/trung bình/cao. Vòng đời: `new → processing → resolved / closed / rejected`; có người được giao xử lý (`assigned_to`). | `reports_interactions/models/ticket_model.py` |
| **QĐ_KTXP_01** | Phiếu khen thưởng / xử phạt | Loại: khen thưởng / xử phạt; có số tiền (VND), người đề xuất, ngày áp dụng, minh chứng. Trạng thái: `pending → approved / rejected`. | `rewards_discipline/models/reward_penalty_model.py` |
| **QĐ_HS_01** | Hồ sơ nhân viên | Hồ sơ gồm các khối tách biệt (cá nhân, công việc, học vấn, liên hệ khẩn cấp, tài liệu); mỗi khối OneToOne với User. HR tạo & quản lý. | `employee_profiles/models/*.py` |

---

## 2. BIỂU MẪU (BM)

### 2.1. Tài khoản & Xác thực — `accounts`

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_DangKyTaiKhoan_01** | Đăng ký tài khoản | `employee_id`, `password`, `full_name`, `email` | `forms/auth/register_form.py` |
| **BM_DangNhap_01** | Đăng nhập | `username`, `password` | `forms/auth/login_form.py` |
| **BM_QuenMatKhau_01** | Nhập username khôi phục | `username` | `forms/auth/forgot_password_form.py` |
| **BM_QuenMatKhau_02** | Nhập mã OTP | `verification_code` (6 số) | `forms/auth/forgot_password_form.py` |
| **BM_DatLaiMatKhau_01** | Đặt lại mật khẩu | `new_password1`, `new_password2` | `forms/auth/reset_password_form.py` |
| **BM_CapNhatTaiKhoan_01** | Cập nhật tài khoản | `full_name`, `phone_number` | `forms/account/account_update_form.py` |
| **BM_TrangThaiTaiKhoan_01** | Khóa / mở tài khoản | `is_active` | `forms/account/account_status_form.py` |
| **BM_GanVaiTro_01** | Gán vai trò | `role` | `forms/account/account_update_form.py` (`AssignRoleForm`) |
| **BM_GanQuyen_01** | Gán quyền tùy chỉnh | `permissions` (nhiều) | `forms/account/account_update_form.py` (`AssignPermissionsForm`) |

### 2.2. Chấm công — `attendance`

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_DieuChinhChamCong_01** | Yêu cầu điều chỉnh chấm công | `reason`, `reason_detail`, `claimed_check_in_time`, `claimed_check_out_time`, `evidence` | `forms/adjustment/attendance_adjustment_form.py` |
| **BM_KhuonMatNhanVien_01** | Đăng ký / cập nhật khuôn mặt | `image_base64`, `content_type` (ảnh chờ HR duyệt) | `models/face_change_request_model.py`, `models/employee_face_model.py` |

### 2.3. Nghỉ phép & Tăng ca — `leaves`, `overtime`

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_DonNghiPhep_01** | Đơn xin nghỉ phép | `leave_type`, `start_date`, `end_date`, `days`, `reason`, `attachment` | `leaves/models/leave_request_model.py` |
| **BM_DonTangCa_01** | Đơn đăng ký tăng ca | `overtime_date`, `start_time`, `end_time`, `hours`, `reason`, `attachment` | `overtime/models/overtime_request_model.py` |

### 2.4. Hợp đồng — `contracts`

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_HopDongLaoDong_01** | Thông tin hợp đồng lao động | `contract_number`, `contract_type`, `contract_signed_date`, `contract_start_date`, `contract_end_date`, `contract_annual_leave_days`, `contract_standard_shift`, `shift_start_time`, `shift_end_time`, `contract_attachment_reference` | `contracts/models/contract_info_model.py` |

### 2.5. Đánh giá, Báo cáo, Ticket, Khen thưởng/Xử phạt

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_DanhGiaNhanVien_01** | Phiếu đánh giá nhân viên | `employee`, `reviewer`, `category`, `score`, `rating`, `evaluation_date`, `content`, `evidence_reference` | `performance/models/evaluation_model.py` |
| **BM_BaoCao_01** | Báo cáo cá nhân | `recipient`, `title`, `content`, `file_attachment` | `reports_interactions/models/report_model.py` |
| **BM_Ticket_01** | Ticket hỗ trợ / khiếu nại | `ticket_type`, `priority`, `title`, `content`, `evidence_file` | `reports_interactions/models/ticket_model.py` |
| **BM_KhenThuongXuPhat_01** | Phiếu khen thưởng / xử phạt | `employee`, `record_type`, `amount`, `reason_title`, `reason_detail`, `application_date`, `evidence_file` | `rewards_discipline/models/reward_penalty_model.py` |

### 2.6. Hồ sơ nhân viên — `employee_profiles`

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_HoSoCaNhan_01** | Thông tin cá nhân | `phone_number`, `date_of_birth`, `gender`, `marital_status`, `nationality`, `id_card_number`, `id_card_issue_place`, `id_card_issue_date`, `permanent_address`, `temporary_address` | `models/personal_info_model.py` |
| **BM_ThongTinCongViec_01** | Thông tin công việc | `employee_type`, `department`, `position`, `workplace`, `probation_start`, `official_start_date`, `work_status`, `manager_user`, `leader_user` | `models/employee_work_info_model.py` |
| **BM_HocVanKyNang_01** | Học vấn & kỹ năng | `education_level`, `degree`, `major`, `certificates`, `foreign_languages`, `professional_skills` | `models/education_skills_model.py` |
| **BM_LienHeKhanCap_01** | Liên hệ khẩn cấp | `contact_name`, `contact_phone`, `relation`, `contact_address` | `models/emergency_contact_model.py` |
| **BM_TaiLieuMinhChung_01** | Tài liệu minh chứng | `title`, `document_type`, `file` | `models/employee_document_model.py` |

---

## 3. Biểu mẫu xử lý / phê duyệt (phía quản lý)

Các thao tác duyệt dùng lại model gốc, bổ sung trường ghi chú/lý do — liệt kê để đầy đủ luồng nghiệp vụ.

| Mã | Tên biểu mẫu | Trường thông tin | Nguồn |
|----|--------------|------------------|-------|
| **BM_DuyetDieuChinhChamCong_01** | HR duyệt điều chỉnh chấm công | `status`, `hr_note`, `reviewed_by`, `reviewed_at` | `attendance/models/attendance_adjustment_request_model.py` |
| **BM_DuyetKhuonMat_01** | HR duyệt cập nhật khuôn mặt | `status`, `hr_note`, `reviewed_by`, `reviewed_at` | `attendance/models/face_change_request_model.py` |
| **BM_DuyetNghiPhep_01** | Duyệt / từ chối nghỉ phép | `status`, `leader_approved_by`, `approved_by`, `rejected_reason` | `leaves/models/leave_request_model.py` |
| **BM_DuyetTangCa_01** | Duyệt / từ chối tăng ca | `status`, `leader_approved_by`, `approved_by`, `rejected_reason` | `overtime/models/overtime_request_model.py` |
| **BM_XacNhanDanhGia_01** | HR xác nhận đánh giá | `acknowledged_by`, `acknowledged_at`, `hr_note` | `performance/models/evaluation_model.py` |
| **BM_PhanHoiBaoCao_01** | Quản lý phản hồi báo cáo | `status`, `manager_note`, `is_viewed`, `viewed_at` | `reports_interactions/models/report_model.py` |
| **BM_XuLyTicket_01** | Xử lý ticket | `status`, `assigned_to`, `rejection_reason` | `reports_interactions/models/ticket_model.py` |
