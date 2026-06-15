# Mapping: Chức năng ↔ File SVG

> Tra cứu nhanh: mỗi chức năng → tên file ảnh trong `docs/diagrams/svg/`.
> Activity & Sequence đánh số per-function (cùng numbering). 10.5 *Cấu hình thông tin công ty* không có trong code → không có hình.

## 1. Activity & Sequence (per-function)

| Chức năng | Activity (.svg) | Sequence (.svg) |
|---|---|---|
| **1. Quản lý tài khoản & phân quyền** | | |
| 1.1 Đăng nhập hệ thống | activity-diagrams-01 | sequence-diagrams-01 |
| 1.2 Đăng xuất hệ thống | activity-diagrams-02 | sequence-diagrams-02 |
| 1.3 Quên mật khẩu bằng OTP | activity-diagrams-03 | sequence-diagrams-03 |
| 1.4 Khóa/Mở khóa tài khoản | activity-diagrams-04 | sequence-diagrams-04 |
| 1.5 Đặt lại mật khẩu nhân viên | activity-diagrams-05 | sequence-diagrams-05 |
| 1.6 Gán vai trò tài khoản | activity-diagrams-06 | sequence-diagrams-06 |
| 1.7 Tạo tài khoản mới | activity-diagrams-07 | sequence-diagrams-07 |
| **2. Quản lý hồ sơ nhân viên** | | |
| 2.1 Xem hồ sơ nhân viên | activity-diagrams-08 | sequence-diagrams-08 |
| 2.2 Tạo nhân viên mới | activity-diagrams-09 | sequence-diagrams-09 |
| 2.3 Chỉnh sửa thông tin cá nhân | activity-diagrams-10 | sequence-diagrams-10 |
| 2.4 Cập nhật thông tin công việc | activity-diagrams-11 | sequence-diagrams-11 |
| 2.5 Quản lý tài liệu nhân viên | activity-diagrams-12 | sequence-diagrams-12 |
| 2.6 Tra cứu danh sách nhân viên | activity-diagrams-13 | sequence-diagrams-13 |
| **3. Quản lý hợp đồng lao động** | | |
| 3.1 Xem hợp đồng lao động | activity-diagrams-14 | sequence-diagrams-14 |
| 3.2 Tạo hợp đồng lao động | activity-diagrams-15 | sequence-diagrams-15 |
| 3.3 Chỉnh sửa hợp đồng lao động | activity-diagrams-16 | sequence-diagrams-16 |
| 3.4 Gia hạn hợp đồng lao động | activity-diagrams-17 | sequence-diagrams-17 |
| 3.5 Cảnh báo hợp đồng sắp hết hạn (Tự động) | activity-diagrams-18 | sequence-diagrams-18 |
| 3.6 Tự động khóa hợp đồng hết hạn (Tự động) | activity-diagrams-19 | sequence-diagrams-19 |
| **4. Quản lý chấm công (FaceID)** | | |
| 4.1 Đăng ký khuôn mặt lần đầu | activity-diagrams-20 | sequence-diagrams-20 |
| 4.2 Cập nhật khuôn mặt | activity-diagrams-21 | sequence-diagrams-21 |
| 4.3 Duyệt yêu cầu đổi khuôn mặt | activity-diagrams-22 | sequence-diagrams-22 |
| 4.4 Chấm công vào (Check-in) | activity-diagrams-23 | sequence-diagrams-23 |
| 4.5 Chấm công ra (Check-out) | activity-diagrams-24 | sequence-diagrams-24 |
| 4.6 Xem lịch sử chấm công | activity-diagrams-25 | sequence-diagrams-25 |
| 4.7 Yêu cầu điều chỉnh giờ công | activity-diagrams-26 | sequence-diagrams-26 |
| 4.8 Duyệt yêu cầu điều chỉnh | activity-diagrams-27 | sequence-diagrams-27 |
| 4.9 Theo dõi trạng thái khuôn mặt | activity-diagrams-28 | sequence-diagrams-28 |
| **5. Quản lý nghỉ phép** | | |
| 5.1 Nộp đơn xin nghỉ phép | activity-diagrams-29 | sequence-diagrams-29 |
| 5.2 Xem đơn nghỉ phép của tôi | activity-diagrams-30 | sequence-diagrams-30 |
| 5.3 Phê duyệt cấp L1 | activity-diagrams-31 | sequence-diagrams-31 |
| 5.4 Phê duyệt cấp L2 | activity-diagrams-32 | sequence-diagrams-32 |
| 5.5 Từ chối đơn nghỉ phép | activity-diagrams-33 | sequence-diagrams-33 |
| 5.6 Xem quỹ phép còn lại | activity-diagrams-34 | sequence-diagrams-34 |
| **6. Quản lý tăng ca (OT)** | | |
| 6.1 Đăng ký tăng ca | activity-diagrams-35 | sequence-diagrams-35 |
| 6.2 Xem đơn tăng ca của tôi | activity-diagrams-36 | sequence-diagrams-36 |
| 6.3 Phê duyệt OT cấp L1 | activity-diagrams-37 | sequence-diagrams-37 |
| 6.4 Phê duyệt OT cấp L2 | activity-diagrams-38 | sequence-diagrams-38 |
| 6.5 Từ chối đơn tăng ca | activity-diagrams-39 | sequence-diagrams-39 |
| **7. Đánh giá hiệu suất (KPI)** | | |
| 7.1 Xem phiếu đánh giá của tôi | activity-diagrams-40 | sequence-diagrams-40 |
| 7.2 Lập phiếu đánh giá | activity-diagrams-41 | sequence-diagrams-41 |
| 7.3 Gửi phiếu đánh giá | activity-diagrams-42 | sequence-diagrams-42 |
| 7.4 Xác nhận phiếu đánh giá | activity-diagrams-43 | sequence-diagrams-43 |
| **8. Khen thưởng & Kỷ luật** | | |
| 8.1 Xem quyết định thưởng/phạt | activity-diagrams-44 | sequence-diagrams-44 |
| 8.2 Đề xuất khen thưởng | activity-diagrams-45 | sequence-diagrams-45 |
| 8.3 Đề xuất xử phạt | activity-diagrams-46 | sequence-diagrams-46 |
| 8.4 Phê duyệt cấp L1 | activity-diagrams-47 | sequence-diagrams-47 |
| 8.5 Phê duyệt cấp L2 | activity-diagrams-48 | sequence-diagrams-48 |
| 8.6 Từ chối đề xuất | activity-diagrams-49 | sequence-diagrams-49 |
| **9. Báo cáo Công việc & Helpdesk Ticket** | | |
| 9.1 Gửi báo cáo công việc | activity-diagrams-50 | sequence-diagrams-50 |
| 9.2 Xem và phản hồi báo cáo | activity-diagrams-51 | sequence-diagrams-51 |
| 9.3 Gửi ticket hỗ trợ/khiếu nại | activity-diagrams-52 | sequence-diagrams-52 |
| 9.4 Xử lý ticket | activity-diagrams-53 | sequence-diagrams-53 |
| **10. Thống kê & Cài đặt hệ thống** | | |
| 10.1 Xem thống kê nhóm trực thuộc (Dashboard Quản lý) | activity-diagrams-54 | sequence-diagrams-54 |
| 10.2 Xem thống kê toàn công ty (Dashboard Admin/HR) | activity-diagrams-55 | sequence-diagrams-55 |
| 10.3 Xuất báo cáo dữ liệu | activity-diagrams-56 | sequence-diagrams-56 |
| 10.4 Cài đặt cá nhân | activity-diagrams-57 | sequence-diagrams-57 |
| 10.5 Cấu hình thông tin công ty | — (không có trong code) | — |
| 10.6 Cấu hình quy định nhân sự | activity-diagrams-58 | sequence-diagrams-58 |

## 2. State Diagrams (vòng đời entity — gộp)

| State / Entity | File (.svg) | Phục vụ chức năng |
|---|---|---|
| ST-CONTRACT — Hợp đồng | state-diagrams-01 | 3.1–3.6 |
| ST-FACECHANGE — Yêu cầu đổi khuôn mặt | state-diagrams-02 | 4.1–4.3, 4.9 |
| ST-ADJUST — Yêu cầu điều chỉnh chấm công | state-diagrams-03 | 4.7–4.8 |
| ST-APPROVAL2 — Đơn duyệt 2 bước (Nghỉ phép + Tăng ca) | state-diagrams-04 | 5.x, 6.x |
| ST-EVAL — Phiếu đánh giá | state-diagrams-05 | 7.x |
| ST-REWARD — Phiếu khen thưởng/xử phạt | state-diagrams-06 | 8.x |
| ST-REPORT — Báo cáo công việc | state-diagrams-07 | 9.1–9.2 |
| ST-TICKET — Ticket hỗ trợ/khiếu nại | state-diagrams-08 | 9.3–9.4 |

---

**Tổng: Activity 58 · Sequence 58 · State 8.** (10.5 không có hình.)
