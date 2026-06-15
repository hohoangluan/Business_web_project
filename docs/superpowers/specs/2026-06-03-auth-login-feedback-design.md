# Gói 1 — Auth login feedback (thông báo lỗi đăng nhập)

Ngày: 2026-06-03. Thuộc kế hoạch lớn (5 gói) cải thiện UI/RBAC toàn hệ thống.

## Vấn đề (có bằng chứng render HTML thật)

1. **Bug A — lỗi login ra tiếng Anh.** Template `accounts/auth/login.html` có nhánh
   tiếng Việt `{% elif form.errors %}` nhưng không bao giờ chạy: `AuthenticationForm`
   luôn đẩy lỗi vào `non_field_errors` (nhánh `if` đầu), in thẳng message mặc định
   tiếng Anh của Django ("Please enter a correct username and password...").
2. **Bug B — thông báo khóa tài khoản không hiện.** `AccountsLoginView._lock_account`
   thêm câu cảnh báo qua `messages.error(...)`, nhưng `login.html` (trang standalone,
   không kế thừa `base_dashboard`) **không có** block `{% if messages %}` → message bị
   mất. User bị khóa mà không biết lý do / không biết liên hệ ai.

Cả 4 case (sai mật khẩu, sai tài khoản, khóa lần thứ 3, TK đã khóa đăng nhập lại) đều
hiển thị cùng câu tiếng Anh — xác nhận bằng cách render HTML response thật.

## Ma trận thông báo (đầu ra mong muốn)

| Tình huống | Thông báo tiếng Việt |
|---|---|
| Sai username/password (TK active) | Tên đăng nhập hoặc mật khẩu không đúng. |
| Username không tồn tại | (cùng câu trên — không tiết lộ tài khoản nào tồn tại) |
| TK đang bị khóa, đăng nhập lại | Tài khoản đã bị khóa. Vui lòng liên hệ HR/Admin để mở khóa. |
| Sai đủ ngưỡng → khóa ngay lần này | Tài khoản đã bị khóa do nhập sai mật khẩu {N} lần. Vui lòng liên hệ HR/Admin để mở khóa. |

`{N}` = `settings.LOGIN_LOCKOUT_MAX_FAILS` (mặc định 3).

## Thiết kế

Nền tảng hiện có (giữ nguyên): bộ đếm sai bằng cache (`login_lockout_service`),
khóa = `is_active=False` (QĐ_TK1), HR/Admin mở khóa (QĐ_TK2). Logic backend đúng,
chỉ thiếu lớp phản hồi UI.

1. **`LoginForm`** (`accounts/forms/auth/login_form.py`): override `error_messages`
   với `invalid_login` và `inactive` bằng tiếng Việt → fix Bug A.
2. **`AccountsLoginView.form_invalid`**: khi `username` tồn tại và `is_active=False`
   (tài khoản đang khóa, không phải vừa khóa lần này) → đẩy message "Tài khoản đã bị
   khóa..." để phân biệt với case sai mật khẩu. `_lock_account` giữ message khó-lần-này.
3. **`login.html`**: thêm block `{% if messages %}` (fix Bug B). Thứ tự ưu tiên:
   có `messages` → chỉ hiện messages (tránh hiện đúp với `non_field_errors`);
   không có messages → hiện `non_field_errors` (giờ đã tiếng Việt).
4. **Tests** (`accounts/tests/test_login.py`): assert **text tiếng Việt trong HTML
   render thật** (`response.content`) thay cho chuỗi tiếng Anh cũ. Thêm case:
   "TK đã khóa đăng nhập lại → thấy message khóa", "khóa lần thứ N → thấy message khóa".

## Tradeoff bảo mật (quyết định có chủ đích)

Hiện "tài khoản đã bị khóa" tiết lộ rằng username đó tồn tại (account enumeration).
Với HRMS nội bộ + yêu cầu sản phẩm muốn user biết để liên hệ HR mở khóa → **chấp nhận**.
Nếu sau này lo enumeration, chuyển sang câu trung lập + gửi hướng dẫn qua kênh khác.

## Phạm vi loại trừ (YAGNI)

Không đụng: cơ chế đếm/khóa (đã chạy), forgot-password, register. Chỉ lớp phản hồi UI
của luồng đăng nhập.
