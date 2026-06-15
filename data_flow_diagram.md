# Data Flow Diagram — Business Web Project

> **Cập nhật:** 2026-06-03 — trích xuất 100% từ code hiện tại.

---

## 1. DFD Context (Level 0)

```mermaid
flowchart LR
    E([Employee]) -->|Đăng ký/Đăng nhập/Chấm công/Tạo đơn/Gửi báo cáo| S[Hệ thống quản lý nhân sự Business Web]
    S -->|Thông báo/Kết quả/Hồ sơ| E
    
    M([Manager/Leader]) -->|Duyệt đơn/Tạo đánh giá/Đề xuất thưởng phạt| S
    S -->|Danh sách cần duyệt/Thống kê nhóm| M
    
    HR([HR]) -->|Duyệt cuối/Quản lý HĐ/Xử lý ticket/Thống kê| S
    S -->|Cảnh báo HĐ/Báo cáo thống kê| HR
    
    AD([Admin]) -->|CRUD user/Gán role-permission/Khóa-mở TK| S
    S -->|Danh sách user| AD
    
    FA([Face Recognition API]) -->|Kết quả nhận diện| S
    S -->|Ảnh khuôn mặt| FA
    
    EM([Gmail SMTP]) -->|Delivery status| S
    S -->|Email OTP/Nhắc HĐ| EM
    
    CL([Cloudinary]) -->|Media URL| S
    S -->|Upload media files| CL
```

---

## 2. DFD Level 1 — Phân rã hệ thống

```mermaid
flowchart TB
    subgraph External
        User([Người dùng])
        FaceAPI([Face Recognition API])
        EmailSvc([Gmail SMTP])
        CloudSvc([Cloudinary])
    end

    subgraph "1.0 Xác thực & Phân quyền"
        P1[1.1 Đăng ký]
        P2[1.2 Đăng nhập + Lockout]
        P3[1.3 Quên mật khẩu + OTP]
        P4[1.4 Quản lý User - Admin]
        P5[1.5 Gán Role/Permission]
        P6[1.6 Thông báo]
    end

    subgraph "2.0 Hồ sơ nhân viên"
        P7[2.1 Xem/Sửa hồ sơ cá nhân]
        P8[2.2 HR tạo hồ sơ]
        P9[2.3 Quản lý thông tin công việc]
        P10[2.4 Upload tài liệu]
    end

    subgraph "3.0 Hợp đồng"
        P11[3.1 Xem HĐ cá nhân]
        P12[3.2 HR quản lý HĐ + Versioning]
        P13[3.3 Cảnh báo HĐ sắp hết hạn]
        P14[3.4 Gửi email nhắc nhở]
    end

    subgraph "4.0 Chấm công"
        P15[4.1 Đăng ký khuôn mặt]
        P16[4.2 Nhận diện + Check-in/out]
        P17[4.3 Yêu cầu điều chỉnh]
        P18[4.4 HR duyệt điều chỉnh]
        P19[4.5 HR duyệt đổi khuôn mặt]
    end

    subgraph "5.0 Nghỉ phép"
        P20[5.1 Tạo/Hủy đơn]
        P21[5.2 Phê duyệt 2 bước]
        P22[5.3 Thống kê phép cá nhân]
    end

    subgraph "6.0 Tăng ca"
        P23[6.1 Tạo/Hủy đơn]
        P24[6.2 Phê duyệt 2 bước]
        P25[6.3 Thống kê tăng ca tháng]
    end

    subgraph "7.0 Đánh giá"
        P26[7.1 Manager/Leader tạo đánh giá]
        P27[7.2 HR xác nhận đánh giá]
    end

    subgraph "8.0 Khen thưởng & Xử phạt"
        P28[8.1 Lập phiếu thưởng/phạt]
        P29[8.2 Phê duyệt 2 cấp]
    end

    subgraph "9.0 Báo cáo & Ticket"
        P30[9.1 Gửi/Sửa/Xóa báo cáo]
        P31[9.2 Manager review báo cáo]
        P32[9.3 Tạo ticket]
        P33[9.4 HR xử lý ticket]
    end

    subgraph "10.0 Thống kê tổng hợp"
        P34[10.1 Thu thập dữ liệu các module]
        P35[10.2 Filter + Aggregate]
        P36[10.3 Export Excel / Print]
    end

    subgraph "Data Stores"
        D1[(User + UserProfile + Role)]
        D2[(PersonalInfo + WorkInfo + Education + Emergency + Document)]
        D3[(ContractInfo)]
        D4[(AttendanceRecord + EmployeeFace + AdjustmentRequest + FaceChangeRequest)]
        D5[(LeaveRequest)]
        D6[(OvertimeRequest)]
        D7[(Evaluation + EvaluationCategory)]
        D8[(RewardPenalty)]
        D9[(Report + Ticket)]
        D10[(OtpCode + Notification)]
        D11[(WorkScheduleConfig)]
    end

    %% Data flows
    User -->|credentials| P2
    User -->|username| P3
    P3 -->|OTP email| EmailSvc
    P1 -->|User+Profile+WorkInfo| D1
    P2 -->|session| User
    P4 -->|CRUD| D1
    P5 -->|role+permission| D1
    P6 -->|read/write| D10

    User -->|personal data| P7
    P7 -->|read/write| D2
    P8 -->|create| D2
    P9 -->|update| D2
    P10 -->|file upload| CloudSvc

    P11 -->|read| D3
    P12 -->|version+write| D3
    P13 -->|query expiring| D3
    P14 -->|reminder email| EmailSvc

    User -->|face image| P15
    P15 -->|register| FaceAPI
    P15 -->|write| D4
    User -->|face image| P16
    P16 -->|recognize| FaceAPI
    P16 -->|write record| D4
    P17 -->|create request| D4
    P18 -->|approve/reject| D4
    P19 -->|approve/reject| D4

    User -->|leave form| P20
    P20 -->|create/delete| D5
    P21 -->|update status| D5
    P22 -->|aggregate| D5

    User -->|overtime form| P23
    P23 -->|create/delete| D6
    P24 -->|update status| D6
    P25 -->|aggregate| D6

    P26 -->|create| D7
    P27 -->|acknowledge| D7

    P28 -->|create| D8
    P29 -->|approve/reject| D8

    User -->|report content| P30
    P30 -->|CRUD| D9
    P31 -->|review| D9
    P32 -->|create| D9
    P33 -->|process| D9

    P34 -->|read| D4
    P34 -->|read| D5
    P34 -->|read| D6
    P34 -->|read| D7
    P34 -->|read| D8
    P35 -->|filtered data| P36
```

---

## 3. DFD Level 2 — Xác thực & Phân quyền chi tiết

```mermaid
flowchart TB
    User([Người dùng])
    
    subgraph "1.0 Xác thực & Phân quyền"
        direction TB
        
        subgraph "1.1 Đăng ký"
            R1[Validate employee_id unique]
            R2[Validate email unique]
            R3[Django password validators]
            R4[Transaction: Create User → UserProfile → WorkInfo]
        end
        
        subgraph "1.2 Đăng nhập"
            L1[Django authenticate]
            L2[Cache: fail counter]
            L3{fail >= LOGIN_LOCKOUT_MAX_FAILS?}
            L4[Set is_active=False]
            L5[Create session]
        end
        
        subgraph "1.3 OTP Recovery"
            O1[Lookup User by username]
            O2[generate_otp: 6 random digits]
            O3[Store OtpCode in DB]
            O4[Send email via SMTP]
            O5[verify_otp: check code + expiry 120s]
            O6[set_password]
        end
        
        subgraph "1.4 Admin Operations"
            A1[User list - filter by role/status]
            A2[Delete user - block self-delete]
            A3[Toggle is_active - block self-toggle]
            A4[Reset password - DEFAULT_RESET_PASSWORD]
            A5[Create account - username + password only]
        end
        
        subgraph "1.5 Role/Permission"
            RP1[Assign Role - 5 choices]
            RP2[Assign CustomPermission - M2M]
        end
    end
    
    D1[(User + UserProfile)]
    D10[(OtpCode)]
    Cache[(Django Cache)]
    Email([Gmail SMTP])
    
    User -->|form data| R1
    R1 --> R2 --> R3 --> R4
    R4 -->|write| D1
    
    User -->|credentials| L1
    L1 -->|fail| L2
    L2 -->|read/write| Cache
    L2 --> L3
    L3 -->|yes| L4
    L4 -->|write| D1
    L1 -->|success| L5
    
    User -->|username| O1
    O1 -->|read| D1
    O1 --> O2 --> O3
    O3 -->|write| D10
    O3 --> O4
    O4 --> Email
    User -->|OTP code| O5
    O5 -->|read| D10
    O5 --> O6
    O6 -->|write| D1
```

---

## 4. DFD Level 2 — Chấm công chi tiết

```mermaid
flowchart TB
    Emp([Employee])
    HR([HR])
    
    subgraph "4.0 Chấm công"
        direction TB
        
        subgraph "4.1 Face Registration"
            FR1[Decode base64 image]
            FR2{Đã có EmployeeFace?}
            FR3[Gọi /register API]
            FR4[Tạo EmployeeFace]
            FR5[Tạo FaceChangeRequest - pending]
        end
        
        subgraph "4.2 Face Check"
            FC1[check_lockout]
            FC2[Gọi /recognize API]
            FC3{Match employee?}
            FC4[record_fail]
            FC5[reset_fails]
            FC6[get_shift_times]
            FC7[log_attendance]
        end
        
        subgraph "4.3 Adjustment"
            AD1[Submit: reason + evidence + claimed times]
            AD2[Create AdjustmentRequest - pending]
        end
        
        subgraph "4.4 HR Review"
            HR1[List pending requests]
            HR2[Approve: update AttendanceRecord]
            HR3[Reject: hr_note]
        end
        
        subgraph "4.5 Face Change Review"
            FCR1[List pending FaceChangeRequests]
            FCR2[Approve: re-register on API]
            FCR3[Reject: hr_note]
        end
    end
    
    FaceAPI([Face Recognition API])
    D4[(AttendanceRecord + EmployeeFace)]
    D3[(ContractInfo)]
    D11[(WorkScheduleConfig)]
    
    Emp -->|image| FR1
    FR1 --> FR2
    FR2 -->|No| FR3
    FR3 --> FaceAPI
    FR3 --> FR4
    FR4 -->|write| D4
    FR2 -->|Yes| FR5
    FR5 -->|write| D4
    
    Emp -->|image| FC1
    FC1 --> FC2
    FC2 --> FaceAPI
    FC2 --> FC3
    FC3 -->|No| FC4
    FC3 -->|Yes| FC5
    FC5 --> FC6
    FC6 -->|read| D3
    FC6 -->|read| D11
    FC6 --> FC7
    FC7 -->|write| D4
    
    Emp -->|adjustment| AD1
    AD1 --> AD2
    AD2 -->|write| D4
    
    HR --> HR1
    HR1 -->|read| D4
    HR --> HR2
    HR2 -->|write| D4
    HR --> HR3
    HR3 -->|write| D4
    
    HR --> FCR1
    FCR1 -->|read| D4
    HR --> FCR2
    FCR2 --> FaceAPI
    FCR2 -->|write| D4
    HR --> FCR3
    FCR3 -->|write| D4
```

---

## 5. DFD Level 2 — Phê duyệt 2 bước (Leaves/Overtime/Rewards)

```mermaid
flowchart TB
    EMP([Employee])
    ML([Manager/Leader])
    HR([HR])
    
    subgraph "Phê duyệt 2 bước"
        direction TB
        
        S1[Employee tạo đơn - status=pending]
        S2[Kiểm tra _is_direct_supervisor]
        S3{Là quản lý trực tiếp?}
        S4{Employee có role HR?}
        S5["status = leader_approved"]
        S6["status = approved - skip L2"]
        S7[Kiểm tra _is_hr_role]
        S8{Là HR?}
        S9["status = approved"]
        S10["Tạo Notification cho employee"]
        S11["status = rejected"]
    end
    
    D_REQ[(LeaveRequest / OvertimeRequest / RewardPenalty)]
    D_WI[(EmployeeWorkInfo)]
    D_N[(Notification)]
    
    EMP -->|form data| S1
    S1 -->|write| D_REQ
    
    ML -->|approve/reject| S2
    S2 -->|read| D_WI
    S2 --> S3
    S3 -->|No| S11
    S3 -->|Yes| S4
    S4 -->|Yes| S6
    S6 -->|write| D_REQ
    S4 -->|No| S5
    S5 -->|write| D_REQ
    
    HR -->|approve/reject| S7
    S7 --> S8
    S8 -->|No| S11
    S8 -->|Yes| S9
    S9 -->|write| D_REQ
    S9 --> S10
    S10 -->|write| D_N
    
    S11 -->|write| D_REQ
    S11 --> S10
```

---

## 6. DFD Level 2 — Thống kê tổng hợp

```mermaid
flowchart TB
    User([HR/Manager/Leader])
    
    subgraph "10.0 Thống kê"
        direction TB
        
        SC[get_statistics_scope]
        SU[get_scope_users]
        SF[build_statistics_filters]
        TR[get_time_range_from_params]
        
        subgraph "Thu thập dữ liệu"
            BD1[build_statistics_records]
            BD2[build_evaluation_records]
            BD3[build_rewards_penalties_records]
        end
        
        FR1[filter_statistics_records]
        FR2[filter_evaluation_records_by_time]
        FR3[filter_rewards_records_by_time]
        
        SM[build_statistics_summary_rows]
        ES[build_evaluation_statistics_sections]
        RS[build_rewards_statistics_sections]
        BS[build_statistics_sections]
        
        OUT1[Render web template]
        OUT2[Export Excel - openpyxl]
        OUT3[Render print template]
    end
    
    D4[(AttendanceRecord)]
    D5[(LeaveRequest)]
    D6[(OvertimeRequest)]
    D7[(Evaluation)]
    D8[(RewardPenalty)]
    
    User --> SC
    SC --> SU
    SU --> SF
    User --> TR
    
    SF --> BD1
    BD1 -->|read| D4
    BD1 -->|read| D5
    BD1 -->|read| D6
    SF --> BD2
    BD2 -->|read| D7
    SF --> BD3
    BD3 -->|read| D8
    
    BD1 --> FR1
    BD2 --> FR2
    BD3 --> FR3
    TR --> FR1
    TR --> FR2
    TR --> FR3
    
    FR1 --> SM
    FR2 --> ES
    FR3 --> RS
    
    SM --> BS
    ES --> BS
    RS --> BS
    
    BS --> OUT1
    BS --> OUT2
    BS --> OUT3
```
