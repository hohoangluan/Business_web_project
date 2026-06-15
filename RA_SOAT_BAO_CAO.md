# Rà soát & Hiệu chỉnh Báo cáo Đồ án

> File kết quả: **`Report_sua.docx`** (gốc `Report.docx` giữ nguyên, backup `Report.docx.bak`).
> Mọi thay đổi đã verify bằng script (mở lại file OK, không hỏng).
>
> 2 quyết định lớn (đã chốt với người dùng):
> 1. **Mã BM/QĐ:** thống nhất hệ **mô tả** (`BM_DangNhap_01`, `QĐ_HD_01`…) — canonical theo `quy_dinh_va_bieu_mau.md` của project.
> 2. **Phân hệ Tính lương:** **CẮT khỏi báo cáo** (chưa hiện thực trong code).

---

## ✅ PHẦN 1 — ĐÃ SỬA XONG TRONG `Report_sua.docx`

### Khớp số liệu với code
- **C1** Auto-logout `30s` → **30 phút** (`SESSION_COOKIE_AGE=1800`).
- **B4** QĐ cảnh báo hợp đồng: thêm mốc **15 ngày** → đủ 30/15/7.
- **C2** `ngayXuPhat` bỏ ràng buộc vô lý "≥ ngày hiện tại theo QĐ14".

### Nhất quán nội bộ
- **B3** Bảng bảo mật 3.3.1.1: căn lại cột Ghi chú 10 dòng (4–13) bị lệch.
- **B6** Bảng quan hệ: xóa dòng "Sở hữu tài khoản" trùng.
- **B8** `super_user` → **Admin** (đồng bộ code chỉ có role `admin`).
- **B9** Mục 7.1: bổ sung **Tailwind CSS**.
- **B10 / 2.8** Caption trùng số: tách **Bảng 3.3.2.2** (yêu cầu công nghệ) & **Bảng 3.3.2.3** (trách nhiệm công nghệ); đánh lại STT Bảng 3.1.3; sửa "thao dõi" → "theo dõi".

### Thống nhất mã BM/QĐ (B1 + B2)
- Sửa các mã **bị dính** trong bảng nghiệp vụ: `BM_GanVaiTro_01BM_GanQuyen_01` → `BM_GanVaiTro_01, BM_GanQuyen_01`; tương tự `BM_HoSoCaNhan_01…`, `BM_QuenMatKhau_01…`, `QĐ_CC_01QĐ_CC_02QĐ_KM_01`, `QĐ_HD_01QĐ_CC_01`, `QĐ_TK_01QĐ_HS_01`, `QĐ_PQ_01QĐ_PQ_02`.
- **Remap toàn bộ mã chương 7** về canonical (31 chỗ): `BM21→BM_DangNhap_01`, `BM4→BM_ThongTinCongViec_01`, `BM1 đến BM7→BM_HoSoCaNhan_01 đến BM_TaiLieuMinhChung_01`, `BM8→BM_HopDongLaoDong_01`, `BM9/BM19→BM_KhuonMatNhanVien_01`, `BM11→BM_DonNghiPhep_01`, `BM12→BM_DonTangCa_01`, `BM17→BM_BaoCao_01`, `BM18→BM_Ticket_01`, `BM22→BM_DieuChinhChamCong_01`, `BM19&BM20→BM_DangKyTaiKhoan_01, BM_GanVaiTro_01`; `QĐ11→QĐ_NP_01`, `QĐ12→QĐ_TC_01`, `QĐ_CanhBao→QĐ_HD_02`, `QĐ_DieuChinh→QĐ_DCCC_01`, `QĐ_DieuHuong/QĐ_ThamQuyenXuLy→QĐ_HT_01`, `QĐ_XacNhanBaoCao→QĐ_BC_01`, `QĐ_PheDuyet_L1/L2→QĐ_NP_01`, `QĐ_CapNhat_HS→QĐ_HS_01`, `QĐ_TK1→"quy định khóa tài khoản"`.
- **Mục 3.1.2**: 18 heading nhóm đổi sang dạng "Nhóm … — gồm: \<các mã canonical\>", xóa hết mã nhóm mồ côi (`BM_TaiKhoanNguoiDung_01`, `QĐ_ChamCong_01`…). → Mọi mã BM/QĐ trong báo cáo giờ **đều định nghĩa được**.

### Class diagram — bảng thuộc tính (2.4 / 2.7)
- **DonNghiPhep**: `ngayNghi/buoiNghi` → `ngayBatDau / ngayKetThuc / soNgay`; trạng thái → `pending → leader_approved → approved / rejected`.
- **ChamCong**: gộp về **1 bản ghi/ngày** (`ngayChamCong + gioVao + gioRa`), trạng thái `on_time / late / early_leave / no_checkout` (bỏ `loaiChamCong`, `ketQua`).
- **YeuCauHoTro (Ticket)**: trạng thái → `new → processing → resolved / closed / rejected`; phân loại → Hỗ trợ / Khiếu nại.
- **2.5 Trưởng phòng**: quan hệ đổi `1—0` → **`0—1`** (có thể trống), khớp class PhongBan + code.

### Logic / nội dung
- **2.3** Bỏ ngưỡng định tuyến duyệt **bịa** ("<2 ngày → Leader", "<4 giờ → Leader"); thay bằng "quản lý trực tiếp duyệt cấp 1 → HR cấp 2, HR tạo đơn chỉ cần 1 cấp".
- **Danh sách lớp (6.2)**: thêm 7 lớp thật (`DonTangCa, KhuonMatNhanVien, DonDoiKhuonMat, DonDieuChinhChamCong, ThongBao, CauHinhGioLam, LoaiDanhGia`); đánh số lại.

### Cắt lương (đã rà toàn bộ)
- Xóa lớp `BangLuong`, `ThongTinLuong` (danh sách lớp + bảng thuộc tính + heading).
- Xóa 2 quan hệ lương; xóa 5 trường lương trong lớp `HopDongLaoDong`.
- Xóa màn **Phiếu lương cá nhân (C&B)** (7.2.6), heading Activity **Tính lương**, heading State **Phiếu lương**, dòng phiếu lương trong bảng ánh xạ 7.3 và RTM.
- Sửa các câu khẳng định phần mềm "tính lương / xuất phiếu lương" ở Mục tiêu (1.2), Khả thi (3.5), Employee Portal (7.1), DFD khen thưởng. **Giữ** các mention thuộc *hiện trạng doanh nghiệp* và *hướng phát triển* (hợp lệ).

### Bổ sung
- **§5.1 Kiến trúc tổng thể** (trước trống): mô tả Django MVT + dịch vụ AI tách rời + PostgreSQL/MongoDB + Gmail SMTP + Render.
- **Phụ lục A**: A.1 Bảng truy vết yêu cầu (RTM), A.2 Tóm tắt kiểm thử, A.3 Ghi chú phạm vi (lương ngoài phạm vi).

---

## 📌 PHẦN 2 — VIỆC CÒN LẠI CHO BẠN (chèn ảnh + refresh)

### 2.1 — Cập nhật Mục lục (TOC)
TOC ở đầu báo cáo là **field tự động**. Sau khi đã xóa mục *Phiếu lương*, *Tính lương* và đổi caption bảng:
→ Mở Word → click vào Mục lục → **Update Field → Update entire table** (hoặc bôi đen toàn bộ rồi **F9**). Làm cho cả "MỤC LỤC" và "MỤC LỤC SƠ ĐỒ".

### 2.2 — VẼ LẠI / CHÈN DIAGRAM (dùng file `.md` sẵn có trong project)

> Các file `.md` dưới đây là **mã nguồn Mermaid/PlantUML đã khớp code**. Render (VD: VS Code Mermaid Preview, mermaid.live, hoặc PlantUML) → xuất PNG → chèn vào đúng vị trí.

| Vị trí trong báo cáo | File nguồn | Ghi chú |
|----------------------|-----------|---------|
| **§6.1 Sơ đồ lớp** (BẮT BUỘC vẽ lại) | `class_diagram.md` | File này đã chuẩn theo code: có đủ 7 lớp mới, không còn lương, DonNghiPhep/ChamCong/Ticket đúng. Render & **thay ảnh class diagram cũ**. |
| **§5.1 Kiến trúc tổng thể** | `deployment_architecture.md` | Chèn sơ đồ kiến trúc/triển khai vào ngay sau đoạn mô tả vừa thêm. |
| §4.2 DFD (các mục con) | `data_flow_diagram.md` | Giữ như cũ; **KHÔNG** chèn DFD nào cho "tính lương". |
| §4.3 Use Case (Package 1–10) | `use_cases.md` | Giữ như cũ. |
| §4.4 Sequence | `sequence_diagrams.md` | Giữ như cũ. |
| §4.5 Activity | `activity_diagrams.md` | Chèn các activity như cũ **TRỪ "Tính lương"** (đã xóa heading). |
| §4.6 State | — | Chèn như cũ **TRỪ "Phiếu lương"** (đã xóa heading). |

**Lưu ý khi vẽ lại class diagram (§6.1):** đảm bảo khớp các sửa đổi đã làm trong bảng thuộc tính —
`DonNghiPhep(start_date,end_date,days)`, `ChamCong(1 record/ngày: check_in_time + check_out_time + status)`, `Ticket(new→processing→resolved/closed/rejected)`, **không có** `BangLuong/ThongTinLuong`, **có** OvertimeRequest/EmployeeFace/FaceChangeRequest/AttendanceAdjustmentRequest/Notification/WorkScheduleConfig/EvaluationCategory.

### 2.3 — Soát mắt 1 lượt (khuyến nghị)
- Đọc lại §7.2.1–7.2.8 (đã đổi mã BM/QĐ) xem câu có mượt không.
- Mục Nhược điểm 8.1.2: có thể thêm 1 câu "Phạm vi bản này chưa bao gồm phân hệ tính lương (C&B)" cho rõ (Phụ lục A.3 đã nêu).

---

## 🎯 PHẦN 3 — Ý KIẾN TĂNG ĐIỂM (tùy chọn)
- Thêm **ERD thật của PostgreSQL** (ngoài class diagram khái niệm).
- Đưa **Phụ lục A (RTM + kiểm thử)** lên cuối chương 3 / chương kiểm thử riêng; bổ sung test case + Bug Log từ `test_plan.md`, `test_result.md`.
- Chèn **ảnh chụp màn hình thật** cho mỗi màn ở chương 7 (minh chứng đã hiện thực).

---

## ✔️ PHẦN 4 — ĐÃ ĐỐI CHIẾU CODE, KHỚP (không cần sửa)
Duyệt 2 cấp nghỉ phép/tăng ca + ngoại lệ HR · OTP 6 số/120s · FaceID 3 lần/300s · ca 08:30–17:30 ân hạn 5' · đánh giá thang 100 A/B/C/D · khen thưởng/xử phạt 2 cấp · ticket new→…→closed · hợp đồng 1 active + versioning + cảnh báo/tự khóa · login khóa 3 lần · session 30' · thống kê tính động + export Excel/CSV/PDF · RBAC + Custom Permission · stack Django/PostgreSQL/MongoDB/FastAPI/DeepFace/Facenet512/HF Space/Gmail SMTP/Render/Tailwind.
