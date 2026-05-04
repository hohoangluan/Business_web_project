/* ============================================================
   HR Studio - JavaScript
   Xử lý tương tác UI: sidebar, password toggle, tabs, modals...
   Code đơn giản, dễ hiểu cho người mới
   ============================================================ */

document.addEventListener('DOMContentLoaded', function() {

  // ============================================================
  // 1. SIDEBAR TOGGLE (Mobile)
  // Mở/đóng sidebar trên màn hình nhỏ
  // ============================================================
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      sidebar.classList.toggle('open');
      if (sidebarOverlay) sidebarOverlay.classList.toggle('show');
    });
  }
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', function() {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('show');
    });
  }

  // ============================================================
  // 2. PASSWORD TOGGLE (Login page)
  // Nút hiện/ẩn mật khẩu
  // ============================================================
  document.querySelectorAll('.toggle-password').forEach(function(btn) {
    btn.addEventListener('click', function() {
      // Tìm input gần nhất trong cùng group
      var input = this.closest('.input-icon-group').querySelector('input');
      var icon = this.querySelector('i');
      if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
      } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
      }
    });
  });

  // ============================================================
  // 3. USER DROPDOWN (Topbar)
  // Menu dropdown khi click vào avatar/tên user
  // ============================================================
  const userMenu = document.querySelector('.user-menu');
  const userDropdown = document.querySelector('.user-dropdown');

  if (userMenu && userDropdown) {
    userMenu.addEventListener('click', function(e) {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });
    // Đóng dropdown khi click ra ngoài
    document.addEventListener('click', function() {
      userDropdown.classList.remove('show');
    });
  }

  // ============================================================
  // 4. PROFILE TABS
  // Chuyển đổi giữa các tab trên trang hồ sơ
  // ============================================================
  const profileTabs = document.querySelectorAll('.profile-tab');
  const profileSections = document.querySelectorAll('.profile-section');

  profileTabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      var target = this.getAttribute('data-tab');

      // Bỏ active tất cả tabs
      profileTabs.forEach(function(t) { t.classList.remove('active'); });
      // Ẩn tất cả sections
      profileSections.forEach(function(s) { s.classList.remove('active'); });

      // Active tab được click
      this.classList.add('active');
      // Hiện section tương ứng
      var section = document.getElementById('section-' + target);
      if (section) section.classList.add('active');
    });
  });

  // ============================================================
  // 5. PROFILE VIEW/EDIT MODE
  // Chuyển đổi giữa chế độ xem và chỉnh sửa
  // ============================================================
  const editBtn = document.getElementById('btnEditProfile');
  const saveBtn = document.getElementById('btnSaveProfile');
  const cancelBtn = document.getElementById('btnCancelEdit');
  const viewMode = document.getElementById('profileViewMode');
  const editMode = document.getElementById('profileEditMode');

  if (editBtn) {
    editBtn.addEventListener('click', function() {
      if (viewMode) viewMode.style.display = 'none';
      if (editMode) editMode.style.display = 'block';
    });
  }
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function() {
      if (viewMode) viewMode.style.display = 'block';
      if (editMode) editMode.style.display = 'none';
    });
  }

  // ============================================================
  // 6. SEARCH & FILTER (User Management)
  // Lọc bảng danh sách user phía client
  // ============================================================
  const searchInput = document.getElementById('userSearch');
  const roleFilter = document.getElementById('roleFilter');
  const statusFilter = document.getElementById('statusFilter');

  function filterTable() {
    var searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    var roleValue = roleFilter ? roleFilter.value : '';
    var statusValue = statusFilter ? statusFilter.value : '';

    var rows = document.querySelectorAll('.data-table tbody tr');
    rows.forEach(function(row) {
      // Lấy text content để search
      var text = row.textContent.toLowerCase();
      var role = row.getAttribute('data-role') || '';
      var status = row.getAttribute('data-status') || '';

      var matchSearch = !searchTerm || text.includes(searchTerm);
      var matchRole = !roleValue || role === roleValue;
      var matchStatus = !statusValue || status === statusValue;

      row.style.display = (matchSearch && matchRole && matchStatus) ? '' : 'none';
    });
  }

  if (searchInput) searchInput.addEventListener('input', filterTable);
  if (roleFilter) roleFilter.addEventListener('change', filterTable);
  if (statusFilter) statusFilter.addEventListener('change', filterTable);

  // ============================================================
  // 7. MODALS
  // Mở/đóng modal dialog
  // ============================================================
  // Mở modal: click vào element có data-modal="modal-id"
  document.querySelectorAll('[data-modal]').forEach(function(trigger) {
    trigger.addEventListener('click', function(e) {
      e.preventDefault();
      var modalId = this.getAttribute('data-modal');
      var modal = document.getElementById(modalId);
      if (modal) modal.classList.add('show');
    });
  });

  // Đóng modal: click nút close hoặc click overlay
  document.querySelectorAll('.modal-close, .modal-cancel').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var overlay = this.closest('.modal-overlay');
      if (overlay) overlay.classList.remove('show');
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === this) this.classList.remove('show');
    });
  });

  // ============================================================
  // 8. CONFIRM ACTIONS
  // Dialog xác nhận cho các hành động nguy hiểm
  // ============================================================
  document.querySelectorAll('[data-confirm]').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      var message = this.getAttribute('data-confirm');
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // ============================================================
  // 9. ALERT DISMISS
  // Đóng thông báo khi click nút X
  // ============================================================
  document.querySelectorAll('.alert-close').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(function() { alert.remove(); }, 300);
      }
    });
  });

  // Tự động ẩn alert sau 5 giây
  document.querySelectorAll('.alert').forEach(function(alert) {
    setTimeout(function() {
      if (alert && alert.parentNode) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(function() { if (alert.parentNode) alert.remove(); }, 300);
      }
    }, 5000);
  });

  // ============================================================
  // 10. DYNAMIC MODAL CONTENT
  // Load nội dung động vào modal (cho xem chi tiết user)
  // ============================================================
  window.openUserDetail = function(userId, username, email, fullName,
                                     employeeId, role, status, dateJoined,
                                     department, position, employeeType, workplace,
                                     probationStart, officialStartDate, workStatus,
                                     managerName, leaderName) {
    var modal = document.getElementById('userDetailModal');
    if (!modal) return;

    // Điền thông tin vào modal
    var setContent = function(id, value) {
      var el = document.getElementById(id);
      if (el) el.textContent = value || '—';
    };
    setContent('detail-fullname', fullName);
    setContent('detail-username', username);
    setContent('detail-email', email);
    setContent('detail-employee-id', employeeId);
    setContent('detail-role', role);
    setContent('detail-status', status);
    setContent('detail-date-joined', dateJoined);
    setContent('detail-department', department);
    setContent('detail-position', position);
    setContent('detail-employee-type', employeeType);
    setContent('detail-workplace', workplace);
    setContent('detail-probation-start', probationStart);
    setContent('detail-official-start-date', officialStartDate);
    setContent('detail-work-status', workStatus);
    setContent('detail-manager-name', managerName);
    setContent('detail-leader-name', leaderName);

    modal.classList.add('show');
  };

  // ============================================================
  // 11. CONFIRM FORM SUBMIT VIA MODAL
  // Xác nhận hành động qua modal (khóa tài khoản, reset mật khẩu)
  // ============================================================
  window.confirmAction = function(actionUrl, actionType, username) {
    var modal = document.getElementById('confirmModal');
    if (!modal) return;

    var titleEl = modal.querySelector('.confirm-title');
    var descEl = modal.querySelector('.confirm-desc');
    var formEl = modal.querySelector('.confirm-form');
    var iconEl = modal.querySelector('.confirm-icon');

    if (actionType === 'lock') {
      if (titleEl) titleEl.textContent = 'Khóa tài khoản';
      if (descEl) descEl.textContent = 'Bạn có chắc muốn khóa tài khoản "' + username + '"?';
      if (iconEl) { iconEl.className = 'fa-solid fa-lock confirm-icon'; iconEl.style.color = '#f59e0b'; }
    } else if (actionType === 'unlock') {
      if (titleEl) titleEl.textContent = 'Mở khóa tài khoản';
      if (descEl) descEl.textContent = 'Bạn có chắc muốn mở khóa tài khoản "' + username + '"?';
      if (iconEl) { iconEl.className = 'fa-solid fa-unlock confirm-icon'; iconEl.style.color = '#10b981'; }
    } else if (actionType === 'reset') {
      if (titleEl) titleEl.textContent = 'Reset mật khẩu';
      if (descEl) descEl.textContent = 'Mật khẩu của "' + username + '" sẽ được reset. Tiếp tục?';
      if (iconEl) { iconEl.className = 'fa-solid fa-key confirm-icon'; iconEl.style.color = '#3b82f6'; }
    }

    if (formEl) formEl.action = actionUrl;
    modal.classList.add('show');
  };

}); // end DOMContentLoaded
