"""
==============================================================================
STATISTICS MODELS
==============================================================================
App thống kê KHÔNG có model riêng.
Nó thu thập và tổng hợp dữ liệu từ các app khác:
  - attendance (chấm công)
  - leaves (nghỉ phép)
  - overtime (tăng ca)
  - performance (đánh giá)
  - rewards_discipline (khen thưởng/xử phạt)

Dữ liệu lấy TRỰC TIẾP từ DB thật của các app trên qua các builder trong
services/ (build_statistics_records, build_evaluation_records,
build_rewards_penalties_records). Không còn mock data.
==============================================================================
"""

# Không có model — app này chỉ đọc dữ liệu từ các app khác.
