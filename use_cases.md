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

> **Lưu ý:** Sơ đồ dùng **Mermaid** để tương thích tốt với hiển thị trên GitHub và các nền tảng markdown hiện đại. Render bằng VSCode (extension *PlantUML*), IntelliJ, hoặc <https://www.plantuml.com/plantuml>. GitHub không render trực tiếp PlantUML.

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

```mermaid
flowchart LR
    %% Actors
    Employee(["🧑‍💼 Nhân viên"])
    Leader(["👨‍💼 Trưởng nhóm"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 Nhân sự HR"])
    Admin(["🛠️ Quản trị viên"])
    FaceAPI["🌐 Remote Face API"]
    SMTP["📧 Gmail SMTP"]

    %% System
    subgraph HRMS["🏢 Hệ thống Quản lý Nhân sự HRMS"]
        direction TB
        subgraph G1["1. Tài khoản & Xác thực"]
            UC_Login("Đăng nhập / Đăng xuất")
            UC_OTP("Quên mật khẩu qua OTP")
            UC_AccMgmt("Quản lý tài khoản")
            UC_RBAC("Phân quyền & Vai trò")
        end
        subgraph G2["2. Hồ sơ & Hợp đồng"]
            UC_ViewProfile("Xem hồ sơ cá nhân")
            UC_CreateProfile("Tạo hồ sơ nhân viên mới")
            UC_EditProfile("Cập nhật hồ sơ nhân viên")
            UC_Contract("Quản lý hợp đồng lao động")
            UC_ContractWarn("Cảnh báo HĐ sắp hết hạn")
        end
        subgraph G3["3. Chấm công & Khuôn mặt"]
            UC_FaceReg("Đăng ký / Cập nhật khuôn mặt")
            UC_FaceApprove("Duyệt yêu cầu đổi khuôn mặt")
            UC_CheckIn("Chấm công vào/ra bằng FaceID")
            UC_History("Xem lịch sử chấm công")
            UC_Adjust("Yêu cầu điều chỉnh giờ công")
            UC_AdjApprove("Duyệt điều chỉnh giờ công")
        end
        subgraph G4["4. Nghỉ phép"]
            UC_Leave("Nộp đơn nghỉ phép")
            UC_LeaveL1("Phê duyệt nghỉ phép L1")
            UC_LeaveL2("Phê duyệt nghỉ phép L2")
        end
        subgraph G5["5. Tăng ca"]
            UC_OT("Đăng ký tăng ca")
            UC_OTL1("Phê duyệt tăng ca L1")
            UC_OTL2("Phê duyệt tăng ca L2")
        end
        subgraph G6["6. Đánh giá hiệu suất"]
            UC_ViewEval("Xem phiếu đánh giá")
            UC_CreateEval("Lập phiếu đánh giá")
            UC_AckEval("Xác nhận đánh giá")
        end
        subgraph G7["7. Khen thưởng & Kỷ luật"]
            UC_ViewRW("Xem quyết định thưởng/phạt")
            UC_ProposeRW("Đề xuất khen thưởng/xử phạt")
            UC_ApproveRW("Duyệt quyết định thưởng/phạt")
        end
        subgraph G8["8. Báo cáo & Hỗ trợ"]
            UC_Report("Gửi báo cáo công việc")
            UC_ReviewReport("Phản hồi báo cáo")
            UC_Ticket("Gửi ticket hỗ trợ/khiếu nại")
            UC_HandleTicket("Xử lý ticket")
        end
        subgraph G9["9. Thống kê"]
            UC_Stats("Xem thống kê tổng hợp")
            UC_Export("Xuất báo cáo dữ liệu")
        end
        subgraph G10["10. Cài đặt hệ thống"]
            UC_Settings("Cài đặt cá nhân")
            UC_CompanyConfig("Cấu hình công ty")
            UC_HRConfig("Cấu hình quy định nhân sự")
        end
    end

    %% Relationships
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
```

---

## 📋 USE CASE CHI TIẾT TỪNG PHÂN HỆ

---

### UC-1. Tài khoản & Xác thực

```mermaid
flowchart LR
    User(["🧑‍💼 Employee/Leader/Manager"])
    HR(["👩‍💻 HR"])
    Admin(["🛠️ Admin"])
    SMTP["📧 Gmail SMTP"]

    subgraph G["Phân hệ Tài khoản & Xác thực"]
        direction TB
        UC1("UC1.1: Đăng nhập hệ thống")
        UC2("UC1.2: Đăng xuất")
        UC3("UC1.3: Quên mật khẩu")
        UC3a("UC1.3a: Gửi OTP qua Email")
        UC3b("UC1.3b: Xác thực OTP & Đổi mật khẩu")
        UC4("UC1.4: Khóa / Mở khóa tài khoản")
        UC5("UC1.5: Reset mật khẩu cho NV")
        UC6("UC1.6: Gán vai trò cho tài khoản")
        UC7("UC1.7: Tạo tài khoản mới")
    end

    User --> UC1
    User --> UC2
    User --> UC3
    UC3 -. "<<include>>" .-> UC3a
    UC3 -. "<<include>>" .-> UC3b
    UC3a --> SMTP

    HR --> UC4
    HR --> UC5

    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    HR(["👩‍💻 HR"])

    subgraph G["Phân hệ Hồ sơ Nhân sự"]
        direction TB
        UC1("UC2.1: Xem hồ sơ cá nhân")
        UC2("UC2.2: Tạo hồ sơ nhân viên mới")
        UC2a("UC2.2a: Tạo username từ MSNV")
        UC2b("UC2.2b: Đặt mật khẩu mặc định")
        UC2c("UC2.2c: Gửi email thông tin tài khoản")
        UC3("UC2.3: Cập nhật thông tin cá nhân")
        UC4("UC2.4: Cập nhật thông tin công việc")
        UC5("UC2.5: Quản lý tài liệu đính kèm")
        UC6("UC2.6: Xem danh sách nhân viên")
    end

    Employee --> UC1

    HR --> UC1
    HR --> UC2
    UC2 -. "<<include>>" .-> UC2a
    UC2 -. "<<include>>" .-> UC2b
    UC2 -. "<<include>>" .-> UC2c
    HR --> UC3
    HR --> UC4
    HR --> UC5
    HR --> UC6
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    HR(["👩‍💻 HR"])

    subgraph G["Phân hệ Hợp đồng Lao động"]
        direction TB
        UC1("UC3.1: Xem hợp đồng của tôi")
        UC2("UC3.2: Tạo hợp đồng mới")
        UC3("UC3.3: Chỉnh sửa hợp đồng")
        UC4("UC3.4: Gia hạn hợp đồng")
        UC5("UC3.5: Cảnh báo HĐ sắp hết hạn")
        UC5a("UC3.5a: Thông báo 30 ngày")
        UC5b("UC3.5b: Thông báo 15 ngày")
        UC5c("UC3.5c: Thông báo KHẨN 7 ngày")
        UC6("UC3.6: Tự động hết hiệu lực")
    end

    Employee --> UC1

    HR --> UC2
    HR --> UC3
    HR --> UC4
    HR --> UC5
    UC5 -. "<<include>>" .-> UC5a
    UC5 -. "<<include>>" .-> UC5b
    UC5 -. "<<include>>" .-> UC5c
    UC5 -. "<<extend>>" .-> UC6
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    HR(["👩‍💻 HR"])
    FaceAPI["🌐 Remote Face API"]

    subgraph G["Phân hệ Chấm công"]
        direction TB
        UC1("UC4.1: Đăng ký khuôn mặt lần đầu")
        UC2("UC4.2: Cập nhật khuôn mặt")
        UC2a("UC4.2a: Tự động duyệt (lần đầu)")
        UC2b("UC4.2b: Chờ HR duyệt (đã có mặt)")
        UC3("UC4.3: Duyệt yêu cầu đổi khuôn mặt")
        UC4("UC4.4: Chấm công vào (Check-in)")
        UC5("UC4.5: Chấm công ra (Check-out)")
        UC4a("UC4.4a: Nhận diện khuôn mặt")
        UC4b("UC4.4b: Xác định trạng thái đúng giờ/trễ")
        UC6("UC4.6: Xem lịch sử chấm công")
        UC7("UC4.7: Yêu cầu điều chỉnh giờ công")
        UC8("UC4.8: Duyệt yêu cầu điều chỉnh")
        UC9("UC4.9: Theo dõi trạng thái khuôn mặt")
    end

    Employee --> UC1
    Employee --> UC2
    UC1 -. "<<include>>" .-> UC2a
    UC2 -. "<<extend>>" .-> UC2b
    Employee --> UC4
    Employee --> UC5
    UC4 -. "<<include>>" .-> UC4a
    UC4 -. "<<include>>" .-> UC4b
    UC5 -. "<<include>>" .-> UC4a
    Employee --> UC6
    Employee --> UC7
    Employee --> UC9

    HR --> UC3
    HR --> UC8

    UC4a --> FaceAPI
    UC2a --> FaceAPI
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    Leader(["👨‍💼 Trưởng nhóm"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 HR"])

    subgraph G["Phân hệ Nghỉ phép"]
        direction TB
        UC1("UC5.1: Nộp đơn xin nghỉ phép")
        UC1a("UC5.1a: Kiểm tra quỹ phép")
        UC2("UC5.2: Xem đơn nghỉ phép của tôi")
        UC3("UC5.3: Phê duyệt cấp L1")
        UC4("UC5.4: Phê duyệt cấp L2")
        UC4a("UC5.4a: Trừ quỹ phép")
        UC5("UC5.5: Từ chối đơn nghỉ phép")
        UC6("UC5.6: Xem quỹ phép còn lại")
    end

    Employee --> UC1
    UC1 -. "<<include>>" .-> UC1a
    Employee --> UC2
    Employee --> UC6

    Leader --> UC3
    Leader --> UC5
    Manager --> UC3
    Manager --> UC5

    HR --> UC4
    UC4 -. "<<include>>" .-> UC4a
    HR --> UC5
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    Leader(["👨‍💼 Trưởng nhóm"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 HR"])

    subgraph G["Phân hệ Tăng ca"]
        direction TB
        UC1("UC6.1: Đăng ký tăng ca")
        UC2("UC6.2: Xem đơn tăng ca của tôi")
        UC3("UC6.3: Phê duyệt OT cấp L1")
        UC4("UC6.4: Phê duyệt OT cấp L2")
        UC4a("UC6.4a: Bỏ qua L2 nếu NV là HR")
        UC5("UC6.5: Từ chối đơn tăng ca")
    end

    Employee --> UC1
    Employee --> UC2

    Leader --> UC3
    Leader --> UC5
    Manager --> UC3
    Manager --> UC5

    HR --> UC4
    UC4 -. "<<extend>>" .-> UC4a
    HR --> UC5
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    Leader(["👨‍💼 Trưởng nhóm"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 HR"])

    subgraph G["Phân hệ Đánh giá"]
        direction TB
        UC1("UC7.1: Xem phiếu đánh giá của tôi")
        UC2("UC7.2: Lập phiếu đánh giá (nháp)")
        UC2a("UC7.2a: Tính điểm & xếp loại tự động")
        UC3("UC7.3: Gửi phiếu đánh giá")
        UC3a("UC7.3a: Khóa chỉnh sửa vĩnh viễn")
        UC4("UC7.4: Xác nhận phiếu đánh giá")
    end

    Employee --> UC1

    Leader --> UC2
    Manager --> UC2
    UC2 -. "<<include>>" .-> UC2a
    Leader --> UC3
    Manager --> UC3
    UC3 -. "<<include>>" .-> UC3a

    HR --> UC4
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    Leader(["👨‍💼 Trưởng nhóm"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 HR"])

    subgraph G["Phân hệ Khen thưởng & Kỷ luật"]
        direction TB
        UC1("UC8.1: Xem quyết định thưởng/phạt")
        UC2("UC8.2: Đề xuất khen thưởng")
        UC3("UC8.3: Đề xuất xử phạt")
        UC4("UC8.4: Phê duyệt cấp L1")
        UC5("UC8.5: Phê duyệt cấp L2")
        UC6("UC8.6: Từ chối đề xuất")
    end

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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    Leader(["👨‍💼 Trưởng nhóm"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 HR"])
    Admin(["🛠️ Admin"])

    subgraph G["Phân hệ Báo cáo & Hỗ trợ"]
        direction TB
        UC1("UC9.1: Gửi báo cáo công việc")
        UC2("UC9.2: Xem & Phản hồi báo cáo")
        UC2a("UC9.2a: Yêu cầu cập nhật lại")
        UC2b("UC9.2b: Xác nhận tiếp nhận")
        UC2c("UC9.2c: Khóa sửa/xóa báo cáo")
        UC3("UC9.3: Gửi ticket hỗ trợ/khiếu nại")
        UC4("UC9.4: Xử lý ticket (tiếp nhận → giải quyết)")
    end

    Employee --> UC1
    Employee --> UC3

    Leader --> UC1

    Manager --> UC2
    UC2 -. "<<extend>>" .-> UC2a
    UC2 -. "<<extend>>" .-> UC2b
    UC2b -. "<<include>>" .-> UC2c

    HR --> UC4
    Admin --> UC4
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

```mermaid
flowchart LR
    Employee(["🧑‍💼 Nhân viên"])
    Manager(["👔 Quản lý"])
    HR(["👩‍💻 HR"])
    Admin(["🛠️ Admin"])

    subgraph G["Phân hệ Thống kê & Cài đặt"]
        direction TB
        UC1("UC10.1: Xem thống kê nhóm trực thuộc")
        UC2("UC10.2: Xem thống kê toàn công ty")
        UC3("UC10.3: Xuất báo cáo dữ liệu")
        UC4("UC10.4: Cài đặt cá nhân")
        UC5("UC10.5: Cấu hình thông tin công ty")
        UC6("UC10.6: Cấu hình quy định nhân sự")
    end

    Employee --> UC4

    Manager --> UC1

    HR --> UC2
    HR --> UC3
    HR --> UC6

    Admin --> UC2
    Admin --> UC5
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
