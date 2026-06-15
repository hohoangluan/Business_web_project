# COVERAGE — Sequence + Activity chi tiết 60 chức năng (+ State khi cần)

> **Scope chốt (override):**
> - ❌ Use-case, Data-flow: **KHÔNG đụng** (giữ hình cũ).
> - ✅ **Activity** + **Sequence**: chi tiết **TỪNG** chức năng trong 60 mục — không bỏ.
> - ✅ **State**: chỉ entity có vòng đời nhiều trạng thái; **được gộp** entity giống nhau.
> - Audit code từng module trước khi vẽ; chức năng code không có → bỏ, ghi rõ (không vẽ hình ma).
> - Sửa ở `.md` gốc (`activity_diagrams.md`, `sequence_diagrams.md`); State viết tay trong `src/` nếu cần.

## Quy ước số
- `ACT-x.y` = Activity cho chức năng x.y · `SEQ-x.y` = Sequence cho chức năng x.y.
- "reuse Ann" = tách/kế thừa từ hình gộp cũ (A=activity hiện có, S=sequence hiện có, CF=code-flow).

## State (gộp) — dự kiến 7 hình
| State | Entity | Trạng thái | Dùng cho |
|---|---|---|---|
| ST-CONTRACT | HopDong | sắp hiệu lực → có hiệu lực → hết hạn/archived | 3.x |
| ST-FACECHANGE | FaceChangeRequest | pending → approved/rejected | 4.2, 4.3, 4.9 |
| ST-ADJUST | AdjustmentRequest | pending → approved/rejected | 4.7, 4.8 |
| ST-APPROVAL2 | Leave + Overtime (gộp) | pending → leader_approved → approved/rejected | 5.x, 6.x |
| ST-REWARD | RewardDiscipline | (Manager: pending→leader_approved→approved) / (Leader: +L1) | 8.x |
| ST-REPORT | Report | submitted → acknowledged / needs_update → submitted | 9.1, 9.2 |
| ST-TICKET | Ticket | new → processing → resolved/rejected | 9.3, 9.4 |

*(Account active/locked = nhị phân → mô tả text, không vẽ State riêng.)*

---

## Index per-function (Activity + Sequence cho cả 60)

### 1. Tài khoản & phân quyền
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 1.1 | Đăng nhập | ACT-1.1 (reuse A2) | SEQ-1.1 (reuse S1) | có lockout |
| 1.2 | Đăng xuất | ACT-1.2 | SEQ-1.2 | logout flush session |
| 1.3 | Quên MK OTP | ACT-1.3 (reuse A3) | SEQ-1.3 (reuse CF3) | |
| 1.4 | Khóa/Mở khóa TK | ACT-1.4 | SEQ-1.4 | admin toggle is_active |
| 1.5 | Reset MK nhân viên | ACT-1.5 | SEQ-1.5 | admin → DEFAULT_RESET |
| 1.6 | Gán vai trò | ACT-1.6 | SEQ-1.6 | role + permissions M2M |
| 1.7 | Tạo TK mới (admin) | ACT-1.7 | SEQ-1.7 | khác self-register A1 |

### 2. Hồ sơ nhân viên
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 2.1 | Xem hồ sơ | ACT-2.1 | SEQ-2.1 | RBAC scope |
| 2.2 | Tạo nhân viên mới | ACT-2.2 | SEQ-2.2 | HR tạo đa bảng |
| 2.3 | Sửa thông tin cá nhân | ACT-2.3 | SEQ-2.3 | |
| 2.4 | Cập nhật thông tin công việc | ACT-2.4 | SEQ-2.4 | manager/leader |
| 2.5 | Quản lý tài liệu NV | ACT-2.5 | SEQ-2.5 | upload doc |
| 2.6 | Tra cứu danh sách NV | ACT-2.6 | SEQ-2.6 | filter/search |

### 3. Hợp đồng (+ ST-CONTRACT)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 3.1 | Xem hợp đồng | ACT-3.1 | SEQ-3.1 (reuse CF8) | + lịch sử |
| 3.2 | Tạo hợp đồng | ACT-3.2 (reuse A7) | SEQ-3.2 | versioning |
| 3.3 | Chỉnh sửa hợp đồng | ACT-3.3 | SEQ-3.3 | archive+new |
| 3.4 | Gia hạn hợp đồng | ACT-3.4 | SEQ-3.4 | |
| 3.5 | Cảnh báo sắp hết hạn (auto) | ACT-3.5 (reuse A13) | SEQ-3.5 (reuse S4) | cron/command |
| 3.6 | Tự khóa HĐ hết hạn (auto) | ACT-3.6 | SEQ-3.6 | expire_overdue |

### 4. Chấm công FaceID (+ ST-FACECHANGE, ST-ADJUST)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 4.1 | Đăng ký khuôn mặt | ACT-4.1 (reuse A6) | SEQ-4.1 (reuse CF5.1) | remote API |
| 4.2 | Cập nhật khuôn mặt | ACT-4.2 | SEQ-4.2 (reuse CF12) | tạo request |
| 4.3 | Duyệt đổi khuôn mặt | ACT-4.3 | SEQ-4.3 | HR approve |
| 4.4 | Check-in | ACT-4.4 (reuse A5) | SEQ-4.4 (reuse S2) | |
| 4.5 | Check-out | ACT-4.5 | SEQ-4.5 | |
| 4.6 | Xem lịch sử chấm công | ACT-4.6 | SEQ-4.6 | |
| 4.7 | Yêu cầu điều chỉnh giờ | ACT-4.7 | SEQ-4.7 | evidence file |
| 4.8 | Duyệt điều chỉnh | ACT-4.8 | SEQ-4.8 | cập nhật record |
| 4.9 | Theo dõi trạng thái khuôn mặt | ACT-4.9 | SEQ-4.9 | |

### 5. Nghỉ phép (+ ST-APPROVAL2)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 5.1 | Nộp đơn nghỉ | ACT-5.1 (reuse A4) | SEQ-5.1 (reuse S3) | auto days |
| 5.2 | Xem đơn của tôi | ACT-5.2 | SEQ-5.2 | |
| 5.3 | Phê duyệt L1 | ACT-5.3 | SEQ-5.3 (reuse CF4) | |
| 5.4 | Phê duyệt L2 | ACT-5.4 | SEQ-5.4 | HR skip nếu HR-emp |
| 5.5 | Từ chối | ACT-5.5 | SEQ-5.5 | |
| 5.6 | Xem quỹ phép còn lại | ❓ACT-5.6 | ❓SEQ-5.6 | **verify code** |

### 6. Tăng ca OT (+ ST-APPROVAL2)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 6.1 | Đăng ký tăng ca | ACT-6.1 | SEQ-6.1 | time validation |
| 6.2 | Xem đơn OT | ACT-6.2 | SEQ-6.2 | |
| 6.3 | Phê duyệt L1 | ACT-6.3 | SEQ-6.3 | |
| 6.4 | Phê duyệt L2 | ACT-6.4 | SEQ-6.4 | |
| 6.5 | Từ chối | ACT-6.5 | SEQ-6.5 | |

### 7. Đánh giá KPI (+ ST-EVAL)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 7.1 | Xem phiếu của tôi | ACT-7.1 | SEQ-7.1 | exclude self |
| 7.2 | Lập phiếu | ACT-7.2 (reuse A10) | SEQ-7.2 (reuse CF11) | score→rating |
| 7.3 | Gửi phiếu | ACT-7.3 | SEQ-7.3 | |
| 7.4 | Xác nhận phiếu | ACT-7.4 | SEQ-7.4 | immutable |

### 8. Khen thưởng & Kỷ luật (+ ST-REWARD)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 8.1 | Xem thưởng/phạt | ACT-8.1 | SEQ-8.1 | scope HR≠Admin |
| 8.2 | Đề xuất khen thưởng | ACT-8.2 (reuse A11) | SEQ-8.2 | |
| 8.3 | Đề xuất xử phạt | ACT-8.3 | SEQ-8.3 | |
| 8.4 | Phê duyệt L1 | ACT-8.4 | SEQ-8.4 | Manager skip-L1 |
| 8.5 | Phê duyệt L2 | ACT-8.5 | SEQ-8.5 | |
| 8.6 | Từ chối | ACT-8.6 | SEQ-8.6 | |

### 9. Báo cáo & Ticket (+ ST-REPORT, ST-TICKET)
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 9.1 | Gửi báo cáo | ACT-9.1 (reuse A8) | SEQ-9.1 (reuse CF7) | |
| 9.2 | Xem & phản hồi báo cáo | ACT-9.2 | SEQ-9.2 | ack/needs_update |
| 9.3 | Gửi ticket | ACT-9.3 (reuse A9) | SEQ-9.3 (reuse CF8) | |
| 9.4 | Xử lý ticket | ACT-9.4 | SEQ-9.4 | |

### 10. Thống kê & Cài đặt
| # | Chức năng | Activity | Sequence | Note |
|---|---|---|---|---|
| 10.1 | Thống kê nhóm | ACT-10.1 (reuse A12) | SEQ-10.1 | manager scope |
| 10.2 | Thống kê toàn cty | ACT-10.2 | SEQ-10.2 | admin/hr |
| 10.3 | Xuất báo cáo dữ liệu | ACT-10.3 | SEQ-10.3 | excel export |
| 10.4 | Cài đặt cá nhân | ACT-10.4 | SEQ-10.4 | ✅ settings/account_update (placeholder UI; sửa cá nhân ở 2.3) |
| 10.5 | Cấu hình thông tin công ty | — | — | ❌ **BỎ — không có model/view trong code** |
| 10.6 | Cấu hình quy định nhân sự | ACT-10.6 | SEQ-10.6 | ✅ settings_view → WorkScheduleConfig |

---

## Khối lượng (thực tế đã build)
- **Activity: 58** · **Sequence: 58** (59 chức năng − bỏ 10.5 không có code = 58 mỗi loại) · **State: 8 gộp**.
- State: ST-CONTRACT · ST-FACECHANGE · ST-ADJUST · ST-APPROVAL2 (leave+OT) · ST-EVAL · ST-REWARD · ST-REPORT · ST-TICKET.
- Verify code: ✅ 5.6 quỹ phép (có) · ✅ 10.4 (placeholder) · ✅ 10.6 (WorkScheduleConfig) · ❌ 10.5 (bỏ — không có).
- Tất cả render SVG nền trắng, 0 fail (trừ 2 overview cũ giữ dạng bảng).

## Thứ tự thực thi (audit code → vẽ → render mỗi module)
1 Accounts → 2 Profiles → 3 Contracts → 4 Attendance → 5 Leaves → 6 Overtime → 7 Performance → 8 Rewards → 9 Reports/Ticket → 10 Stats/Settings → render toàn bộ 0 fail.
