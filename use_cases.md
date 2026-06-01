# 📊 Sơ Đồ Use Case — Hệ Thống HRMS

> **Hệ thống Quản lý Nhân sự (Human Resource Management System)**
> Môn học: SE104 – Nhập môn Công nghệ Phần mềm

---

## Quy ước ký hiệu

| Ký hiệu | Ý nghĩa |
|----------|----------|
| `actor` | Tác nhân (Actor) — hình người (stick figure) |
| `<<system>>` | Tác nhân hệ thống ngoài (External system) |
| `usecase` | Use Case — hình ellipse bo tròn |
| `-->` | Tương tác trực tiếp (Association) |
| `..>` | Quan hệ `<<include>>` hoặc `<<extend>>` |
| `rectangle` | Ranh giới hệ thống (System Boundary) |

> **Lưu ý:** Sơ đồ dùng **PlantUML** để actor hiển thị dạng stick figure. Render bằng VSCode (extension *PlantUML*), IntelliJ, hoặc <https://www.plantuml.com/plantuml>. GitHub không render trực tiếp PlantUML.

---

## 👥 Danh sách Tác nhân (Actors)

| Actor | Vai trò | Mô tả |
|-------|---------|-------|
| **Nhân viên (Employee)** | `employee` | Tác nhân cơ bản. Mọi user đều là nhân viên. |
| **Trưởng nhóm (Leader)** | `leader` | Quản lý trực tiếp cấp nhóm. Phê duyệt L1, đánh giá, đề xuất thưởng/phạt. |
| **Quản lý (Manager)** | `manager` | Quản lý cấp phòng ban. Phê duyệt L1, đánh giá, phản hồi báo cáo. |
| **Nhân sự (HR)** | `hr` | Quản lý hồ sơ, hợp đồng, phê duyệt L2, điều chỉnh công. |
| **Quản trị viên (Admin)** | `admin` | Quản lý tài khoản hệ thống, phân quyền, cấu hình. |
| **Service nhận diện (Remote API)** | External | Service từ xa (FastAPI + DeepFace). |
| **Gmail SMTP** | External | Gửi OTP đặt lại mật khẩu. |

---

## 🗺️ USE CASE TỔNG QUÁT — Toàn bộ Hệ thống

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Trưởng nhóm" as Leader
actor "Quản lý" as Manager
actor "Nhân sự HR" as HR
actor "Quản trị viên" as Admin
actor "Remote Face API" as FaceAPI <<system>>
actor "Gmail SMTP" as SMTP <<system>>

rectangle "🏢 Hệ thống Quản lý Nhân sự HRMS" {

    rectangle "1. Tài khoản & Xác thực" {
        usecase "Đăng nhập / Đăng xuất" as UC_Login
        usecase "Quên mật khẩu qua OTP" as UC_OTP
        usecase "Quản lý tài khoản" as UC_AccMgmt
        usecase "Phân quyền & Vai trò" as UC_RBAC
    }

    rectangle "2. Hồ sơ & Hợp đồng" {
        usecase "Xem hồ sơ cá nhân" as UC_ViewProfile
        usecase "Tạo hồ sơ nhân viên mới" as UC_CreateProfile
        usecase "Cập nhật hồ sơ nhân viên" as UC_EditProfile
        usecase "Quản lý hợp đồng lao động" as UC_Contract
        usecase "Cảnh báo HĐ sắp hết hạn" as UC_ContractWarn
    }

    rectangle "3. Chấm công & Khuôn mặt" {
        usecase "Đăng ký / Cập nhật khuôn mặt" as UC_FaceReg
        usecase "Duyệt yêu cầu đổi khuôn mặt" as UC_FaceApprove
        usecase "Chấm công vào/ra bằng FaceID" as UC_CheckIn
        usecase "Xem lịch sử chấm công" as UC_History
        usecase "Yêu cầu điều chỉnh giờ công" as UC_Adjust
        usecase "Duyệt điều chỉnh giờ công" as UC_AdjApprove
    }

    rectangle "4. Nghỉ phép" {
        usecase "Nộp đơn nghỉ phép" as UC_Leave
        usecase "Phê duyệt nghỉ phép L1" as UC_LeaveL1
        usecase "Phê duyệt nghỉ phép L2" as UC_LeaveL2
    }

    rectangle "5. Tăng ca" {
        usecase "Đăng ký tăng ca" as UC_OT
        usecase "Phê duyệt tăng ca L1" as UC_OTL1
        usecase "Phê duyệt tăng ca L2" as UC_OTL2
    }

    rectangle "6. Đánh giá hiệu suất" {
        usecase "Xem phiếu đánh giá" as UC_ViewEval
        usecase "Lập phiếu đánh giá" as UC_CreateEval
        usecase "Xác nhận đánh giá" as UC_AckEval
    }

    rectangle "7. Khen thưởng & Kỷ luật" {
        usecase "Xem quyết định thưởng/phạt" as UC_ViewRW
        usecase "Đề xuất khen thưởng/xử phạt" as UC_ProposeRW
        usecase "Duyệt quyết định thưởng/phạt" as UC_ApproveRW
    }

    rectangle "8. Báo cáo & Hỗ trợ" {
        usecase "Gửi báo cáo công việc" as UC_Report
        usecase "Phản hồi báo cáo" as UC_ReviewReport
        usecase "Gửi ticket hỗ trợ/khiếu nại" as UC_Ticket
        usecase "Xử lý ticket" as UC_HandleTicket
    }

    rectangle "9. Thống kê" {
        usecase "Xem thống kê tổng hợp" as UC_Stats
        usecase "Xuất báo cáo dữ liệu" as UC_Export
    }

    rectangle "10. Cài đặt hệ thống" {
        usecase "Cài đặt cá nhân" as UC_Settings
        usecase "Cấu hình công ty" as UC_CompanyConfig
        usecase "Cấu hình quy định nhân sự" as UC_HRConfig
    }
}

Employee --> UC_Login
Employee --> UC_OTP
Employee --> UC_ViewProfile
Employee --> UC_FaceReg
Employee --> UC_CheckIn
Employee --> UC_History
Employee --> UC_Adjust
Employee --> UC_Leave
Employee --> UC_OT
Employee --> UC_ViewEval
Employee --> UC_ViewRW
Employee --> UC_Report
Employee --> UC_Ticket
Employee --> UC_Settings

Leader --> UC_LeaveL1
Leader --> UC_OTL1
Leader --> UC_CreateEval
Leader --> UC_ProposeRW
Leader --> UC_ReviewReport

Manager --> UC_LeaveL1
Manager --> UC_OTL1
Manager --> UC_CreateEval
Manager --> UC_ProposeRW
Manager --> UC_ReviewReport
Manager --> UC_Stats

HR --> UC_CreateProfile
HR --> UC_EditProfile
HR --> UC_Contract
HR --> UC_ContractWarn
HR --> UC_FaceApprove
HR --> UC_AdjApprove
HR --> UC_LeaveL2
HR --> UC_OTL2
HR --> UC_AckEval
HR --> UC_ApproveRW
HR --> UC_HandleTicket
HR --> UC_Stats
HR --> UC_Export
HR --> UC_HRConfig
HR --> UC_AccMgmt

Admin --> UC_AccMgmt
Admin --> UC_RBAC
Admin --> UC_CompanyConfig
Admin --> UC_Stats
Admin --> UC_HandleTicket

FaceAPI --> UC_FaceReg
FaceAPI --> UC_CheckIn
SMTP --> UC_OTP
@enduml
```

---

## 📋 USE CASE CHI TIẾT TỪNG PHÂN HỆ

---

### UC-1. Tài khoản & Xác thực

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Employee/Leader/Manager" as User
actor HR
actor Admin
actor "Gmail SMTP" as SMTP <<system>>

rectangle "Phân hệ Tài khoản & Xác thực" {
    usecase "UC1.1: Đăng nhập hệ thống" as UC1
    usecase "UC1.2: Đăng xuất" as UC2
    usecase "UC1.3: Quên mật khẩu" as UC3
    usecase "UC1.3a: Gửi OTP qua Email" as UC3a
    usecase "UC1.3b: Xác thực OTP & Đổi mật khẩu" as UC3b
    usecase "UC1.4: Khóa / Mở khóa tài khoản" as UC4
    usecase "UC1.5: Reset mật khẩu cho NV" as UC5
    usecase "UC1.6: Gán vai trò cho tài khoản" as UC6
    usecase "UC1.7: Tạo tài khoản mới" as UC7
}

User --> UC1
User --> UC2
User --> UC3
UC3 ..> UC3a : <<include>>
UC3 ..> UC3b : <<include>>
UC3a --> SMTP

HR --> UC4
HR --> UC5

Admin --> UC4
Admin --> UC5
Admin --> UC6
Admin --> UC7
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC1.1 | Nhập username + password. Kiểm tra `is_active`, xác thực, tạo session. | Nhân viên |
| UC1.2 | Hủy session đăng nhập, redirect về trang login. | Nhân viên |
| UC1.3 | Nhập email → nhận OTP 6 số (hết hạn 120 giây) → nhập OTP + mật khẩu mới. | Nhân viên |
| UC1.4 | Đặt `is_active = False/True` cho tài khoản nhân viên. HR chỉ thao tác Employee/Leader/Manager. Admin thao tác mọi tài khoản. | HR, Admin |
| UC1.5 | Tạo mật khẩu mới cho nhân viên (khi quên email hoặc bị khóa). | HR, Admin |
| UC1.6 | Gán vai trò (`admin`, `hr`, `manager`, `leader`, `employee`) cho tài khoản. | Admin |
| UC1.7 | Tạo tài khoản Django User mới, gán role ban đầu. | Admin |

---

### UC-2. Hồ sơ Nhân sự

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor HR

rectangle "Phân hệ Hồ sơ Nhân sự" {
    usecase "UC2.1: Xem hồ sơ cá nhân" as UC1
    usecase "UC2.2: Tạo hồ sơ nhân viên mới" as UC2
    usecase "UC2.2a: Tạo username từ MSNV" as UC2a
    usecase "UC2.2b: Đặt mật khẩu mặc định" as UC2b
    usecase "UC2.2c: Gửi email thông tin tài khoản" as UC2c
    usecase "UC2.3: Cập nhật thông tin cá nhân" as UC3
    usecase "UC2.4: Cập nhật thông tin công việc" as UC4
    usecase "UC2.5: Quản lý tài liệu đính kèm" as UC5
    usecase "UC2.6: Xem danh sách nhân viên" as UC6
}

Employee --> UC1

HR --> UC1
HR --> UC2
UC2 ..> UC2a : <<include>>
UC2 ..> UC2b : <<include>>
UC2 ..> UC2c : <<include>>
HR --> UC3
HR --> UC4
HR --> UC5
HR --> UC6
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC2.1 | Xem thông tin cá nhân, công việc, học vấn, liên hệ khẩn cấp. NV chỉ xem của mình, HR xem tất cả. | Nhân viên, HR |
| UC2.2 | HR điền form tạo NV mới: **tự nhập MSNV (employee_id)**, thông tin cá nhân, công việc, upload ảnh khuôn mặt. | HR |
| UC2.2a | Hệ thống tạo username = MSNV viết thường, bỏ khoảng trắng; kiểm tra trùng. | Hệ thống |
| UC2.2b | Hệ thống đặt mật khẩu mặc định `{MSNV}@2026`. | Hệ thống |
| UC2.2c | Gửi email chứa username + mật khẩu mặc định cho NV mới. | Hệ thống |
| UC2.3 | HR chỉnh sửa thông tin cá nhân (SĐT, địa chỉ, CCCD...). | HR |
| UC2.4 | HR cập nhật thông tin công việc (phòng ban, chức danh, trạng thái, quản lý). | HR |
| UC2.5 | Upload/xóa tài liệu đính kèm hồ sơ nhân viên. | HR |
| UC2.6 | Xem danh sách toàn bộ nhân viên với bộ lọc, tìm kiếm. | HR |

---

### UC-3. Hợp đồng Lao động

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor HR

rectangle "Phân hệ Hợp đồng Lao động" {
    usecase "UC3.1: Xem hợp đồng của tôi" as UC1
    usecase "UC3.2: Tạo hợp đồng mới" as UC2
    usecase "UC3.3: Chỉnh sửa hợp đồng" as UC3
    usecase "UC3.4: Gia hạn hợp đồng" as UC4
    usecase "UC3.5: Cảnh báo HĐ sắp hết hạn" as UC5
    usecase "UC3.5a: Thông báo 30 ngày" as UC5a
    usecase "UC3.5b: Thông báo 15 ngày" as UC5b
    usecase "UC3.5c: Thông báo KHẨN 7 ngày" as UC5c
    usecase "UC3.6: Tự động hết hiệu lực" as UC6
}

Employee --> UC1

HR --> UC2
HR --> UC3
HR --> UC4
HR --> UC5
UC5 ..> UC5a : <<include>>
UC5 ..> UC5b : <<include>>
UC5 ..> UC5c : <<include>>
UC5 ..> UC6 : <<extend>>
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC3.1 | NV xem danh sách HĐ đã ký, HĐ đang hiệu lực (`is_active=True`). | Nhân viên |
| UC3.2 | HR tạo HĐ mới: loại HĐ, ngày ký, ngày hiệu lực, ngày hết hạn, ca làm, ngày phép. | HR |
| UC3.3 | HR chỉnh sửa nội dung HĐ chưa hết hiệu lực. | HR |
| UC3.4 | HR gia hạn HĐ cũ (tạo HĐ mới, đóng HĐ cũ `is_active=False`). | HR |
| UC3.5 | Batch job tự động cảnh báo tại mốc 30/15/7 ngày trước khi HĐ hết hạn. | Hệ thống |
| UC3.6 | HĐ quá hạn mà chưa gia hạn → tự động `is_active=False`. | Hệ thống |

---

### UC-4. Chấm công & Nhận diện Khuôn mặt

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor HR
actor "Remote Face API" as FaceAPI <<system>>

rectangle "Phân hệ Chấm công" {
    usecase "UC4.1: Đăng ký khuôn mặt lần đầu" as UC1
    usecase "UC4.2: Cập nhật khuôn mặt" as UC2
    usecase "UC4.2a: Tự động duyệt (lần đầu)" as UC2a
    usecase "UC4.2b: Chờ HR duyệt (đã có mặt)" as UC2b
    usecase "UC4.3: Duyệt yêu cầu đổi khuôn mặt" as UC3
    usecase "UC4.4: Chấm công vào (Check-in)" as UC4
    usecase "UC4.5: Chấm công ra (Check-out)" as UC5
    usecase "UC4.4a: Nhận diện khuôn mặt" as UC4a
    usecase "UC4.4b: Xác định trạng thái đúng giờ/trễ" as UC4b
    usecase "UC4.6: Xem lịch sử chấm công" as UC6
    usecase "UC4.7: Yêu cầu điều chỉnh giờ công" as UC7
    usecase "UC4.8: Duyệt yêu cầu điều chỉnh" as UC8
    usecase "UC4.9: Theo dõi trạng thái khuôn mặt" as UC9
}

Employee --> UC1
Employee --> UC2
UC1 ..> UC2a : <<include>>
UC2 ..> UC2b : <<extend>>
Employee --> UC4
Employee --> UC5
UC4 ..> UC4a : <<include>>
UC4 ..> UC4b : <<include>>
UC5 ..> UC4a : <<include>>
Employee --> UC6
Employee --> UC7
Employee --> UC9

HR --> UC3
HR --> UC8

UC4a --> FaceAPI
UC2a --> FaceAPI
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC4.1 | NV chưa có `EmployeeFace` → chụp ảnh → **tự động duyệt**, áp dụng ngay lập tức. | Nhân viên |
| UC4.2 | NV đã có khuôn mặt → chụp ảnh mới → tạo `FaceChangeRequest(pending)` → **chờ HR duyệt**. | Nhân viên |
| UC4.3 | HR xem danh sách yêu cầu, duyệt hoặc từ chối kèm ghi chú lý do. Duyệt → đẩy ảnh lên Remote API và cập nhật `EmployeeFace`. | HR |
| UC4.4 | NV nhấn nút chấm công → webcam chụp ảnh → gửi lên hệ thống → nhận diện khuôn mặt qua Remote API → ghi `check_in_time`. | Nhân viên |
| UC4.5 | Tương tự UC4.4 nhưng ghi `check_out_time`. | Nhân viên |
| UC4.6 | Xem bảng lịch sử chấm công trong tháng (ngày, giờ vào, giờ ra, trạng thái). | Nhân viên |
| UC4.7 | NV gửi yêu cầu điều chỉnh giờ công (quên chấm, lỗi kỹ thuật) kèm minh chứng. | Nhân viên |
| UC4.8 | HR xem yêu cầu điều chỉnh, duyệt (cập nhật giờ công) hoặc từ chối. | HR |
| UC4.9 | NV xem trạng thái khuôn mặt: Chưa đăng ký / Chờ duyệt / Bị từ chối / Đang hoạt động. | Nhân viên |

---

### UC-5. Nghỉ phép

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Trưởng nhóm" as Leader
actor "Quản lý" as Manager
actor HR

rectangle "Phân hệ Nghỉ phép" {
    usecase "UC5.1: Nộp đơn xin nghỉ phép" as UC1
    usecase "UC5.1a: Kiểm tra quỹ phép" as UC1a
    usecase "UC5.2: Xem đơn nghỉ phép của tôi" as UC2
    usecase "UC5.3: Phê duyệt cấp L1" as UC3
    usecase "UC5.4: Phê duyệt cấp L2" as UC4
    usecase "UC5.4a: Trừ quỹ phép" as UC4a
    usecase "UC5.5: Từ chối đơn nghỉ phép" as UC5
    usecase "UC5.6: Xem quỹ phép còn lại" as UC6
}

Employee --> UC1
UC1 ..> UC1a : <<include>>
Employee --> UC2
Employee --> UC6

Leader --> UC3
Leader --> UC5
Manager --> UC3
Manager --> UC5

HR --> UC4
UC4 ..> UC4a : <<include>>
HR --> UC5
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC5.1 | NV chọn loại phép (`annual`, `sick`, `personal`...), khoảng ngày, lý do, đính kèm minh chứng. Hệ thống kiểm tra quỹ phép. | Nhân viên |
| UC5.2 | NV xem danh sách đơn đã nộp và trạng thái (pending → leader_approved → approved / rejected). | Nhân viên |
| UC5.3 | Leader/Manager (là `leader_user` hoặc `manager_user` của NV) duyệt cấp 1. | Leader, Manager |
| UC5.4 | HR duyệt cấp 2 sau khi L1 đã duyệt. Duyệt thành công → trừ quỹ phép. | HR |
| UC5.5 | L1 hoặc L2 từ chối đơn, ghi lý do. | Leader, Manager, HR |
| UC5.6 | NV xem số ngày phép còn lại theo hợp đồng. | Nhân viên |

---

### UC-6. Tăng ca (OT)

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Trưởng nhóm" as Leader
actor "Quản lý" as Manager
actor HR

rectangle "Phân hệ Tăng ca" {
    usecase "UC6.1: Đăng ký tăng ca" as UC1
    usecase "UC6.2: Xem đơn tăng ca của tôi" as UC2
    usecase "UC6.3: Phê duyệt OT cấp L1" as UC3
    usecase "UC6.4: Phê duyệt OT cấp L2" as UC4
    usecase "UC6.4a: Bỏ qua L2 nếu NV là HR" as UC4a
    usecase "UC6.5: Từ chối đơn tăng ca" as UC5
}

Employee --> UC1
Employee --> UC2

Leader --> UC3
Leader --> UC5
Manager --> UC3
Manager --> UC5

HR --> UC4
UC4 ..> UC4a : <<extend>>
HR --> UC5
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC6.1 | NV chọn ngày OT, giờ bắt đầu/kết thúc, lý do, đính kèm minh chứng. | Nhân viên |
| UC6.2 | NV xem danh sách đơn OT đã nộp và trạng thái. | Nhân viên |
| UC6.3 | Leader/Manager duyệt cấp 1 đơn OT. | Leader, Manager |
| UC6.4 | HR duyệt cấp 2. **Ngoại lệ:** Nếu người tạo đơn có role HR → sau L1 chuyển thẳng `approved`. | HR |
| UC6.5 | L1 hoặc L2 từ chối đơn, ghi lý do. | Leader, Manager, HR |

---

### UC-7. Đánh giá Hiệu suất

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Trưởng nhóm" as Leader
actor "Quản lý" as Manager
actor HR

rectangle "Phân hệ Đánh giá" {
    usecase "UC7.1: Xem phiếu đánh giá của tôi" as UC1
    usecase "UC7.2: Lập phiếu đánh giá (nháp)" as UC2
    usecase "UC7.2a: Tính điểm & xếp loại tự động" as UC2a
    usecase "UC7.3: Gửi phiếu đánh giá" as UC3
    usecase "UC7.3a: Khóa chỉnh sửa vĩnh viễn" as UC3a
    usecase "UC7.4: Xác nhận phiếu đánh giá" as UC4
}

Employee --> UC1

Leader --> UC2
Manager --> UC2
UC2 ..> UC2a : <<include>>
Leader --> UC3
Manager --> UC3
UC3 ..> UC3a : <<include>>

HR --> UC4
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC7.1 | NV xem danh sách phiếu đánh giá mình đã nhận, điểm số, xếp loại. | Nhân viên |
| UC7.2 | Leader/Manager tạo phiếu nháp: chọn NV, loại đánh giá, nhập score (0–100), nội dung, minh chứng. Hệ thống **tự tính** rating A/B/C/D từ score khi `save()`. | Leader, Manager |
| UC7.3 | Leader/Manager nhấn gửi → `status=submitted` → **khóa vĩnh viễn** không thể chỉnh sửa. | Leader, Manager |
| UC7.4 | HR xem phiếu đánh giá, thêm `hr_note`, xác nhận → `status=acknowledged`. | HR |

---

### UC-8. Khen thưởng & Kỷ luật

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Trưởng nhóm" as Leader
actor "Quản lý" as Manager
actor HR

rectangle "Phân hệ Khen thưởng & Kỷ luật" {
    usecase "UC8.1: Xem quyết định thưởng/phạt" as UC1
    usecase "UC8.2: Đề xuất khen thưởng" as UC2
    usecase "UC8.3: Đề xuất xử phạt" as UC3
    usecase "UC8.4: Phê duyệt cấp L1" as UC4
    usecase "UC8.5: Phê duyệt cấp L2" as UC5
    usecase "UC8.6: Từ chối đề xuất" as UC6
}

Employee --> UC1

Leader --> UC2
Leader --> UC3
Manager --> UC2
Manager --> UC3
HR --> UC2
HR --> UC3

Manager --> UC4

HR --> UC5
HR --> UC6
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC8.1 | NV xem quyết định thưởng/phạt của mình. | Nhân viên |
| UC8.2 | Leader/Manager/HR lập phiếu khen thưởng: chọn NV, lý do, số tiền, minh chứng. | Leader, Manager, HR |
| UC8.3 | Leader/Manager/HR lập phiếu xử phạt: chọn NV, lý do, số tiền, minh chứng. | Leader, Manager, HR |
| UC8.4 | Manager duyệt L1 nếu Leader lập phiếu. Manager lập → bỏ qua L1, chuyển thẳng HR. | Manager |
| UC8.5 | HR duyệt L2 để ban hành quyết định chính thức. | HR |
| UC8.6 | HR từ chối đề xuất. | HR |

---

### UC-9. Báo cáo Công việc & Helpdesk Ticket

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Trưởng nhóm" as Leader
actor "Quản lý" as Manager
actor HR
actor Admin

rectangle "Phân hệ Báo cáo & Hỗ trợ" {
    usecase "UC9.1: Gửi báo cáo công việc" as UC1
    usecase "UC9.2: Xem & Phản hồi báo cáo" as UC2
    usecase "UC9.2a: Yêu cầu cập nhật lại" as UC2a
    usecase "UC9.2b: Xác nhận tiếp nhận" as UC2b
    usecase "UC9.2c: Khóa sửa/xóa báo cáo" as UC2c
    usecase "UC9.3: Gửi ticket hỗ trợ/khiếu nại" as UC3
    usecase "UC9.4: Xử lý ticket (tiếp nhận → giải quyết)" as UC4
}

Employee --> UC1
Employee --> UC3

Leader --> UC1

Manager --> UC2
UC2 ..> UC2a : <<extend>>
UC2 ..> UC2b : <<extend>>
UC2b ..> UC2c : <<include>>

HR --> UC4
Admin --> UC4
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC9.1 | NV/Leader gửi báo cáo (tiêu đề, nội dung, file). Employee → gửi Leader; Leader → gửi Manager. | Nhân viên, Leader |
| UC9.2 | Manager/Leader xem báo cáo → `is_viewed=True`. | Manager, Leader |
| UC9.2a | Yêu cầu NV cập nhật lại → `status=needs_update`. | Manager, Leader |
| UC9.2b | Xác nhận tiếp nhận → `status=acknowledged` → **khóa** sửa/xóa. | Manager, Leader |
| UC9.3 | NV tạo ticket (loại: hỗ trợ/khiếu nại, mức ưu tiên, nội dung, file). Ticket ở `status=new`, **chưa gán** người xử lý. | Nhân viên |
| UC9.4 | Người có quyền tự nhận ticket (`assigned_to=self`, `processing`) → `resolved` → NV xác nhận (`closed`); hoặc `rejected` kèm lý do. | HR, Admin |

---

### UC-10. Thống kê & Cài đặt

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

actor "Nhân viên" as Employee
actor "Quản lý" as Manager
actor HR
actor Admin

rectangle "Phân hệ Thống kê & Cài đặt" {
    usecase "UC10.1: Xem thống kê nhóm trực thuộc" as UC1
    usecase "UC10.2: Xem thống kê toàn công ty" as UC2
    usecase "UC10.3: Xuất báo cáo dữ liệu" as UC3
    usecase "UC10.4: Cài đặt cá nhân" as UC4
    usecase "UC10.5: Cấu hình thông tin công ty" as UC5
    usecase "UC10.6: Cấu hình quy định nhân sự" as UC6
}

Employee --> UC4

Manager --> UC1

HR --> UC2
HR --> UC3
HR --> UC6

Admin --> UC2
Admin --> UC5
@enduml
```

**Mô tả chi tiết:**

| Use Case | Mô tả | Actor |
|----------|-------|-------|
| UC10.1 | Manager/Leader xem thống kê chấm công, nghỉ phép, OT của nhân viên mình quản lý. | Manager |
| UC10.2 | HR/Admin xem dashboard thống kê tổng hợp toàn công ty. | HR, Admin |
| UC10.3 | HR xuất dữ liệu ra file báo cáo. | HR |
| UC10.4 | NV tùy chỉnh giao diện (dark mode, ngôn ngữ, thông báo email). | Nhân viên |
| UC10.5 | Admin cấu hình tên công ty, mã số thuế, email hệ thống. | Admin |
| UC10.6 | HR cấu hình giờ làm chuẩn, ngưỡng đi trễ, số ngày phép mặc định, giới hạn OT. | HR |
