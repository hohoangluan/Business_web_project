# 📊 Sơ Đồ Activity (Activity Diagrams) — Hệ Thống HRMS

> **Hệ thống Quản lý Nhân sự (Human Resource Management System)**
> Môn học: SE104 – Nhập môn Công nghệ Phần mềm

---

## Quy ước ký hiệu

| Ký hiệu Mermaid | Ý nghĩa UML Activity |
|------------------|----------------------|
| `([...])` | Nút bắt đầu / Kết thúc |
| `[...]` | Hành động (Action) |
| `{...}` | Nút quyết định (Decision) |
| `-->` | Luồng điều khiển (Control Flow) |
| Swimlane (`subgraph`) | Phân vùng trách nhiệm (Partition) |

---

## AD-1. Đăng nhập Hệ thống

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Nhân viên mở trang đăng nhập"]
    A1 --> A2["Nhập Username + Password"]
    A2 --> D1{"Tài khoản tồn tại?"}
    D1 -- Không --> E1["Hiển thị: Sai thông tin đăng nhập"]
    E1 --> A2
    D1 -- Có --> D2{"Tài khoản bị khóa?"}
    D2 -- Có --> E2["Hiển thị: Tài khoản bị khóa"]
    E2 --> End1(["⚪ Kết thúc"])
    D2 -- Không --> D3{"Mật khẩu đúng?"}
    D3 -- Sai --> A5["register_failure(username)<br/>tăng đếm qua cache"]
    A5 --> D4{"Đạt 3 lần sai liên tiếp?<br/>LOGIN_LOCKOUT_MAX_FAILS"}
    D4 -- Có --> E4["Khóa is_active=False<br/>Hiển thị: Tài khoản đã bị khóa"]
    E4 --> End3(["⚪ Kết thúc"])
    D4 -- Chưa --> E3["Hiển thị: Sai thông tin đăng nhập"]
    E3 --> A2
    D3 -- Đúng --> A3["clear_failures(username)<br/>Tạo Session"]
    A3 --> A4["Redirect tới /dashboard/<br/>(1 trang, nội dung theo Role)"]
    A4 --> End2(["⚪ Kết thúc"])
```

---

## AD-2. Quên mật khẩu (OTP qua Email)

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Nhân viên nhấn 'Quên mật khẩu'"]
    A1 --> A2["Nhập địa chỉ Email"]
    A2 --> D1{"Email tồn tại trong hệ thống?"}
    D1 -- Không --> E1["Hiển thị: Email không tìm thấy"]
    E1 --> End1(["⚪ Kết thúc"])
    D1 -- Có --> A3["Hệ thống sinh mã OTP 6 chữ số"]
    A3 --> A4["Lưu OtpCode vào Database"]
    A4 --> A5["Gửi OTP qua Gmail SMTP"]
    A5 --> A6["Nhân viên nhập OTP + Mật khẩu mới"]
    A6 --> D2{"OTP đúng?"}
    D2 -- Sai --> E2["Hiển thị: Mã OTP không đúng"]
    E2 --> A6
    D2 -- Đúng --> D3{"OTP còn hạn? <= 120 giây"}
    D3 -- Hết hạn --> E3["Hiển thị: OTP đã hết hạn"]
    E3 --> A2
    D3 -- Còn hạn --> A7["Cập nhật mật khẩu mới"]
    A7 --> A8["Xóa OtpCode"]
    A8 --> A9["Hiển thị: Đổi mật khẩu thành công"]
    A9 --> End2(["⚪ Kết thúc"])
```

---

## AD-3. Tạo Hồ sơ Nhân viên Mới (HR)

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["HR điền form hồ sơ nhân viên"]
    A1 --> A2["Nhập thông tin cá nhân, công việc, hợp đồng"]
    A2 --> A3["Upload ảnh khuôn mặt"]
    A3 --> D1{"Dữ liệu hợp lệ?<br/>MSNV không rỗng & chưa tồn tại,<br/>department bắt buộc"}
    D1 -- Không --> E1["Hiển thị lỗi validation"]
    E1 --> A2
    D1 -- Có --> A4["Username = MSNV viết thường,<br/>bỏ khoảng trắng"]
    A4 --> D1b{"Username đã tồn tại?"}
    D1b -- Có --> E1
    D1b -- Không --> A5["Đặt mật khẩu mặc định<br/>{MSNV}@2026"]
    A5 --> A6["Tạo User (create_user)"]
    A6 --> A7["Tạo UserProfile (employee_id=MSNV, role)"]
    A7 --> A8["Tạo PersonalInfo, EmployeeWorkInfo"]
    A8 --> A10["Đăng ký khuôn mặt lên Remote API"]
    A10 --> D2{"Remote API thành công?"}
    D2 -- Lỗi --> E2["Hiển thị lỗi đăng ký khuôn mặt"]
    E2 --> End1(["⚪ Kết thúc"])
    D2 -- Thành công --> A11["Tạo EmployeeFace + FaceChangeRequest approved"]
    A11 --> A12["Gửi email tài khoản cho NV mới"]
    A12 --> A13["Hiển thị: Tạo hồ sơ thành công"]
    A13 --> End2(["⚪ Kết thúc"])
```

---

## AD-4. Đăng ký / Cập nhật Khuôn mặt

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Nhân viên vào Cài đặt > Khuôn mặt nhận diện"]
    A1 --> A2["Xem trạng thái khuôn mặt hiện tại"]
    A2 --> D0{"Có yêu cầu đang chờ duyệt?"}
    D0 -- Có --> E0["Nút upload bị vô hiệu hóa<br/>Hiển thị: Chờ HR duyệt"]
    E0 --> End0(["⚪ Kết thúc"])
    D0 -- Không --> A3["Nhấn 'Đăng ký / Cập nhật khuôn mặt'"]
    A3 --> A4["Mở webcam, chụp ảnh"]
    A4 --> A5["Gửi ảnh lên server<br/>POST /attendance/upload-image/"]
    A5 --> D1{"MIME type hợp lệ?"}
    D1 -- Không --> E1["Hiển thị: Loại file không hợp lệ"]
    E1 --> End1(["⚪ Kết thúc"])
    D1 -- Có --> D2{"Nhân viên đã có khuôn mặt?"}
    D2 -- "Chưa có (Lần đầu)" --> A6["Gọi Remote API /register"]
    A6 --> D3{"API thành công?"}
    D3 -- Lỗi --> E2["Hiển thị lỗi<br/>VD: Không phát hiện khuôn mặt"]
    E2 --> End2(["⚪ Kết thúc"])
    D3 -- Thành công --> A7["Tạo EmployeeFace"]
    A7 --> A8["Tạo FaceChangeRequest<br/>status=approved, auto-duyệt"]
    A8 --> A9["Hiển thị: Đăng ký thành công<br/>Trạng thái: Đang hoạt động ✅"]
    A9 --> End3(["⚪ Kết thúc"])
    D2 -- "Đã có (Cập nhật)" --> A10["Xóa FaceChangeRequest pending cũ"]
    A10 --> A11["Tạo FaceChangeRequest mới<br/>status=pending"]
    A11 --> A12["Hiển thị: Đã gửi yêu cầu<br/>Trạng thái: Chờ HR duyệt ⏳"]
    A12 --> End4(["⚪ Kết thúc"])
```

---

## AD-5. HR Duyệt Yêu cầu Đổi Khuôn mặt

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["HR mở trang Duyệt cập nhật khuôn mặt"]
    A1 --> A2["Xem danh sách yêu cầu pending"]
    A2 --> A3["Chọn một yêu cầu để xem chi tiết"]
    A3 --> D1{"HR quyết định?"}
    D1 -- Duyệt --> A4["Đọc ảnh từ FaceChangeRequest"]
    A4 --> A5["Gọi Remote API /register với ảnh mới"]
    A5 --> D2{"API thành công?"}
    D2 -- Lỗi --> E1["Hiển thị: Service từ chối ảnh"]
    E1 --> End1(["⚪ Kết thúc"])
    D2 -- Thành công --> A6["Cập nhật EmployeeFace"]
    A6 --> A7["status=approved<br/>Ghi reviewed_by, reviewed_at"]
    A7 --> A8["Hiển thị: Đã duyệt thành công"]
    A8 --> End2(["⚪ Kết thúc"])
    D1 -- Từ chối --> A9["Nhập lý do từ chối hr_note"]
    A9 --> A10["status=rejected<br/>Ghi reviewed_by, reviewed_at"]
    A10 --> A11["NV thấy trạng thái: Bị từ chối ❌<br/>kèm lý do"]
    A11 --> End3(["⚪ Kết thúc"])
```

---

## AD-6. Chấm công bằng FaceID

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Nhân viên mở trang Chấm công"]
    A1 --> A2["Nhấn nút Chấm công"]
    A2 --> A3["Mở webcam, chụp ảnh"]
    A3 --> A4["Gửi ảnh lên server<br/>POST /attendance/check/"]
    A4 --> D1{"Bị khóa lockout?<br/>3 lần sai → khóa 300s"}
    D1 -- Có --> E1["Hiển thị: Đã khóa<br/>Thử lại sau N giây"]
    E1 --> End1(["⚪ Kết thúc"])
    D1 -- Không --> A5["Gọi Remote API /recognize"]
    A5 --> D2{"API phản hồi?"}
    D2 -- "Lỗi / Service down" --> E2["Hiển thị: Dịch vụ chưa sẵn sàng"]
    E2 --> End2(["⚪ Kết thúc"])
    D2 -- "Không phát hiện mặt" --> E3["Hiển thị: Không tìm thấy khuôn mặt"]
    E3 --> End3(["⚪ Kết thúc"])
    D2 -- Nhận diện OK --> D3{"employee_id khớp user hiện tại?"}
    D3 -- "Không khớp (wrong_person)" --> A6["Tăng đếm lockout"]
    A6 --> E4["Hiển thị: Khuôn mặt không khớp<br/>Còn N lần thử"]
    E4 --> End4(["⚪ Kết thúc"])
    D3 -- Khớp đúng --> D4{"Xác định hành động?"}
    D4 -- Check-in --> D5{"Giờ hiện tại <= shift_start + grace?"}
    D5 -- Có --> A7["Ghi check_in_time<br/>status = on_time"]
    D5 -- Không --> A8["Ghi check_in_time<br/>status = late"]
    A7 --> A9["Hiển thị: Chấm vào thành công lúc HH:MM"]
    A8 --> A9
    D4 -- Check-out --> D6{"Giờ hiện tại < shift_end?"}
    D6 -- Có --> A10["Ghi check_out_time<br/>status = early_leave"]
    D6 -- Không --> A11["Ghi check_out_time<br/>Giữ status"]
    A10 --> A12["Hiển thị: Chấm ra thành công lúc HH:MM"]
    A11 --> A12
    D4 -- "Đã chấm đủ" --> E5["Hiển thị: Bạn đã chấm công hôm nay"]
    E5 --> End5(["⚪ Kết thúc"])
    A9 --> A13["Xóa đếm lockout"]
    A12 --> A13
    A13 --> End6(["⚪ Kết thúc"])
```

---

## AD-7. Yêu cầu Điều chỉnh Giờ công

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["NV xem lịch sử chấm công"]
    A1 --> A2["Nhấn 'Yêu cầu điều chỉnh' cho ngày cần sửa"]
    A2 --> A3["Chọn lý do: Quên chấm / Lỗi kỹ thuật /<br/>Công tác / Khác"]
    A3 --> A4["Nhập giờ vào/ra thực tế khai báo"]
    A4 --> A5["Nhập chi tiết lý do + Upload minh chứng"]
    A5 --> A6["Gửi yêu cầu<br/>AdjustmentRequest status=pending"]
    A6 --> A7["HR nhận yêu cầu vào trang Duyệt"]
    A7 --> D1{"HR quyết định?"}
    D1 -- Duyệt --> A8["Cập nhật check_in/check_out<br/>theo giờ khai báo"]
    A8 --> A9["Tính lại trạng thái<br/>on_time / late / early_leave"]
    A9 --> A10["status=approved<br/>Ghi hr_note"]
    A10 --> End1(["⚪ Kết thúc"])
    D1 -- Từ chối --> A11["status=rejected<br/>Ghi lý do từ chối"]
    A11 --> End2(["⚪ Kết thúc"])
```

---

## AD-8. Nghỉ phép — Phê duyệt 2 cấp

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Nhân viên mở trang Nghỉ phép"]
    A1 --> A2["Chọn loại phép, khoảng ngày,<br/>lý do, đính kèm minh chứng"]
    A2 --> A3["Tạo LeaveRequest<br/>days = end-start+1, status=pending"]
    A3 --> A4["Thông báo tới Leader/Manager<br/>người quản lý trực tiếp của NV"]
    A4 --> D2{"Leader/Manager quyết định L1?"}
    D2 -- Từ chối --> A5["status=rejected<br/>Ghi lý do từ chối"]
    A5 --> End2(["⚪ Kết thúc"])
    D2 -- Duyệt L1 --> A6["status=leader_approved<br/>Ghi leader_approved_by + at"]
    A6 --> A7["Chuyển đơn tới HR duyệt L2"]
    A7 --> D3{"HR quyết định L2?"}
    D3 -- Từ chối --> A8["status=rejected<br/>Ghi lý do từ chối"]
    A8 --> End3(["⚪ Kết thúc"])
    D3 -- Duyệt L2 --> A9["status=approved<br/>Ghi approved_by"]
    A9 --> A10["Quỹ phép còn lại tự cập nhật<br/>(derived: Σ ngày đơn approved trong năm)"]
    A10 --> End4(["⚪ Kết thúc"])
```

---

## AD-9. Tăng ca (OT) — Phê duyệt 2 cấp

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["NV mở trang Tăng ca"]
    A1 --> A2["Nhập ngày OT, giờ bắt đầu/kết thúc,<br/>lý do, đính kèm"]
    A2 --> A3["Tạo OvertimeRequest<br/>status=pending"]
    A3 --> A4["Thông báo tới Leader/Manager"]
    A4 --> D1{"Leader/Manager quyết định L1?"}
    D1 -- Từ chối --> A5["status=rejected"]
    A5 --> End1(["⚪ Kết thúc"])
    D1 -- Duyệt L1 --> A6["status=leader_approved"]
    A6 --> D2{"Người tạo đơn có role HR?"}
    D2 -- Có --> A7["status=approved<br/>Bỏ qua L2"]
    A7 --> End2(["⚪ Kết thúc"])
    D2 -- Không --> A8["Chuyển đơn tới HR duyệt L2"]
    A8 --> D3{"HR quyết định L2?"}
    D3 -- Từ chối --> A9["status=rejected"]
    A9 --> End3(["⚪ Kết thúc"])
    D3 -- Duyệt L2 --> A10["status=approved"]
    A10 --> End4(["⚪ Kết thúc"])
```

---

## AD-10. Đánh giá Nhân viên

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Leader/Manager mở trang Đánh giá"]
    A1 --> A2["Chọn nhân viên cần đánh giá"]
    A2 --> A3["Chọn loại đánh giá<br/>Chuyên cần, Hiệu suất, Kỹ năng nhóm..."]
    A3 --> A4["Nhập điểm score 0–100"]
    A4 --> A5["Hệ thống tự tính rating<br/>A: >=90, B: >=75, C: >=60, D: <60"]
    A5 --> A6["Nhập nội dung đánh giá + Minh chứng"]
    A6 --> A7["Lưu nháp<br/>Evaluation status=draft"]
    A7 --> D1{"Sẵn sàng gửi?"}
    D1 -- "Chưa (tiếp tục chỉnh)" --> A4
    D1 -- "Gửi" --> A8["status=submitted<br/>🔒 Khóa chỉnh sửa vĩnh viễn"]
    A8 --> A9["Thông báo tới HR"]
    A9 --> A10["HR xem phiếu đánh giá"]
    A10 --> A11["HR thêm ghi chú hr_note"]
    A11 --> A12["HR nhấn Xác nhận<br/>status=acknowledged"]
    A12 --> End1(["⚪ Kết thúc"])
```

---

## AD-11. Khen thưởng / Xử phạt — Phê duyệt 2 cấp

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["Leader/Manager/HR lập phiếu<br/>Khen thưởng hoặc Xử phạt"]
    A1 --> A2["Chọn nhân viên, nhập lý do,<br/>số tiền, minh chứng"]
    A2 --> A3["Tạo RewardPenalty<br/>status=pending"]
    A3 --> D1{"Người lập là ai?"}
    D1 -- Leader --> A4["Chuyển Manager duyệt L1"]
    A4 --> D2{"Manager quyết định L1?"}
    D2 -- Từ chối --> E1["status=rejected"]
    E1 --> End1(["⚪ Kết thúc"])
    D2 -- Duyệt L1 --> A5["status=leader_approved<br/>Ghi leader_approved_by + at<br/>Chuyển HR duyệt L2"]
    D1 -- "Manager / HR" --> A5
    A5 --> D3{"HR quyết định L2?"}
    D3 -- Từ chối --> E2["status=rejected"]
    E2 --> End2(["⚪ Kết thúc"])
    D3 -- Duyệt L2 --> A6["status=approved<br/>Ghi approved_by · Thông báo NV<br/>Ban hành quyết định"]
    A6 --> End3(["⚪ Kết thúc"])
```

---

## AD-12. Báo cáo Công việc

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["NV/Leader tạo báo cáo<br/>Tiêu đề, nội dung, file đính kèm"]
    A1 --> A2["Hệ thống xác định người nhận<br/>Employee → Leader, Leader → Manager"]
    A2 --> A3["Tạo Report<br/>status=submitted, is_viewed=False"]
    A3 --> A4["Quản lý mở xem báo cáo"]
    A4 --> A5["is_viewed=True, viewed_at=now"]
    A5 --> D1{"Quản lý quyết định?"}
    D1 -- "Cần bổ sung" --> A6["Nhập ghi chú manager_note<br/>status=needs_update"]
    A6 --> A7["NV chỉnh sửa và gửi lại"]
    A7 --> A4
    D1 -- "Tiếp nhận" --> A8["status=acknowledged"]
    A8 --> A9["🔒 Khóa sửa/xóa báo cáo<br/>can_edit_or_delete=False"]
    A9 --> End1(["⚪ Kết thúc"])
```

---

## AD-13. Helpdesk Ticket — Tiếp nhận & Xử lý

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu"])
    Start --> A1["NV mở trang Hỗ trợ & Khiếu nại"]
    A1 --> A2["Chọn loại: Hỗ trợ / Khiếu nại<br/>Nhập tiêu đề, nội dung, mức ưu tiên, file"]
    A2 --> A3["Tạo Ticket<br/>status=new, assigned_to=null"]
    A3 --> A4["Người có quyền xử lý (HR/Admin)<br/>mở trang Xử lý ticket"]
    A4 --> D1{"Quyết định?"}
    D1 -- "Tiếp nhận" --> A5["assigned_to = self<br/>status=processing"]
    A5 --> A6["Xử lý vấn đề"]
    A6 --> A7["status=resolved"]
    A7 --> A8["NV xác nhận đã giải quyết"]
    A8 --> A9["status=closed"]
    A9 --> End1(["⚪ Kết thúc"])
    D1 -- "Từ chối" --> A10["status=rejected<br/>Ghi rejection_reason"]
    A10 --> End2(["⚪ Kết thúc"])
```

---

## AD-14. Cảnh báo Hợp đồng Hết hạn (Batch Job)

```mermaid
flowchart TD
    Start(["⚫ Bắt đầu<br/>Batch Job chạy 1-3h AM mỗi ngày"])
    Start --> A1["Lấy ContractInfo is_active=True,<br/>contract_end_date != ''"]
    A1 --> A2["Duyệt từng hợp đồng<br/>days_left = end_date - today"]
    A2 --> D1{"days_left?"}
    D1 -- "0 < days_left <= 7 (gần/khẩn)" --> A5["Cảnh báo KHẨN<br/>NV + Manager + Leader + tất cả HR"]
    D1 -- "0 < days_left <= 30 (xa)" --> A3["Cảnh báo<br/>NV + Manager + Leader + tất cả HR"]
    D1 -- "days_left < 0 (đã hết hạn)" --> A6["is_active=False<br/>Hợp đồng hết hiệu lực"]
    D1 -- "Chưa đến mốc / không thời hạn" --> A8["Bỏ qua"]
    A3 --> A9{"Còn HĐ tiếp theo?"}
    A5 --> A9
    A6 --> A9
    A8 --> A9
    A9 -- Có --> A2
    A9 -- Không --> End1(["⚪ Kết thúc"])
```
