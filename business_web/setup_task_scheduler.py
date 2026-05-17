"""
==============================================================================
SETUP WINDOWS TASK SCHEDULER
==============================================================================
Script tạo Windows Scheduled Task để chạy lệnh nhắc gia hạn HĐ lúc 0:00 hàng ngày.

Cách dùng:
  1. Mở PowerShell với quyền Administrator
  2. Chạy: python setup_task_scheduler.py

Hoặc chạy file PowerShell trực tiếp:
  .\\schedule_contract_reminder.ps1
==============================================================================
"""

import subprocess
import sys
import os

# Đường dẫn đến Python executable và manage.py
PYTHON_PATH = sys.executable
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MANAGE_PY   = os.path.join(BASE_DIR, 'manage.py')
LOG_DIR     = os.path.join(BASE_DIR, 'logs')
LOG_FILE    = os.path.join(LOG_DIR, 'contract_reminder.log')

TASK_NAME   = "HRStudio_ContractRenewalReminder"
TASK_DESC   = "HR Studio - Gửi email nhắc gia hạn hợp đồng lúc 0:00 mỗi ngày"

# Lệnh chạy Django management command
COMMAND     = f'"{PYTHON_PATH}" "{MANAGE_PY}" send_contract_renewal_reminders --days=30'


def create_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"[OK] Thư mục log: {LOG_DIR}")


def create_powershell_script():
    """Tạo script PowerShell bọc lệnh Python, ghi log."""
    ps_path = os.path.join(BASE_DIR, 'schedule_contract_reminder.ps1')
    content = f"""# HR Studio - Contract Renewal Reminder Runner
# Chạy bởi Windows Task Scheduler lúc 0:00 mỗi ngày

$PythonPath = "{PYTHON_PATH}"
$ManagePy   = "{MANAGE_PY}"
$LogFile    = "{LOG_FILE}"

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$Timestamp] === Bat dau kiem tra hop dong ===" | Out-File -FilePath $LogFile -Append -Encoding UTF8

try {{
    & $PythonPath $ManagePy send_contract_renewal_reminders --days=30 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
    "[$Timestamp] === Hoan tat ===" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}} catch {{
    "[$Timestamp] [ERROR] $_" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}}
"""
    with open(ps_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[OK] Script PowerShell: {ps_path}")
    return ps_path


def register_task(ps_path):
    """Đăng ký Scheduled Task chạy lúc 0:00 mỗi ngày."""
    # Xóa task cũ nếu có
    subprocess.run(
        ['schtasks', '/delete', '/tn', TASK_NAME, '/f'],
        capture_output=True
    )

    result = subprocess.run([
        'schtasks', '/create',
        '/tn',  TASK_NAME,
        '/tr',  f'powershell.exe -ExecutionPolicy Bypass -File "{ps_path}"',
        '/sc',  'daily',
        '/st',  '00:00',
        '/rl',  'highest',
        '/f',
        '/ru',  'SYSTEM',
        '/td',  f'{TASK_DESC}',
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Task '{TASK_NAME}' đã được đăng ký thành công!")
        print(f"     Chạy lúc: 0:00 hàng ngày")
        print(f"     Log tại:  {LOG_FILE}")
    else:
        print(f"[FAIL] Đăng ký task thất bại:")
        print(result.stderr or result.stdout)
        print("\nThử chạy PowerShell script thủ công:")
        print(f"  powershell -ExecutionPolicy Bypass -File \"{ps_path}\"")


if __name__ == '__main__':
    print("=" * 60)
    print("  HR Studio — Setup Windows Task Scheduler")
    print("=" * 60)
    create_log_dir()
    ps_path = create_powershell_script()
    register_task(ps_path)
    print("\nKiểm tra task đã tạo:")
    print(f"  schtasks /query /tn {TASK_NAME}")
    print("=" * 60)
