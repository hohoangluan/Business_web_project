# Diagram SVG — báo cáo Word

**162 sơ đồ** render **SVG nền trắng** (vector — phóng to không vỡ, Word 2016+ chèn trực tiếp `Insert → Pictures`).
Đã **đối chiếu code thật** (view/service/model) trước khi xuất. Ma trận phủ 60 chức năng: `COVERAGE.md`.

> **Activity & Sequence nay là PER-FUNCTION** — mỗi chức năng (1.1 → 10.6) 1 hình riêng (58 mỗi loại;
> bỏ 10.5 *Cấu hình thông tin công ty* vì không có trong code). State diagram (8 hình) cho entity có vòng đời.

> **3 sơ đồ tổng quan KHÔNG xuất ảnh** (quá khổ, dán Word bị nhỏ) → để dạng văn bản/bảng trong file `.md`:
> DFD Level 1 (`data_flow_diagram.md` §2, 20:1), Use Case tổng quát (`use_cases.md` §tổng quát, cao ~8 trang),
> ERD overview. Dùng các bản chi tiết/tách bên dưới thay thế.

- `src/` — file `.mmd` nguồn (mermaid).
- `svg/` — ảnh kết quả để dán báo cáo.
- Render lại: `npm`/`npx @mermaid-js/mermaid-cli` với `mermaid.config.json` + `puppeteer.config.json` (xem cuối file).

> **Tip Word**: chèn SVG xong, kéo theo bề ngang trang (~16cm). Vector nên chữ luôn nét.
> Sơ đồ rộng (toàn cảnh) → đặt trang **Landscape** hoặc dùng bản tách module.

---

## ERD — PostgreSQL thật (tách module cho dễ đọc)

| Section báo cáo | File SVG |
|---|---|
| Accounts (tài khoản & phân quyền) | `svg/erd-01-accounts.svg` |
| Employee Profiles (hồ sơ NV) | `svg/erd-02-profiles.svg` |
| Attendance (chấm công) | `svg/erd-03-attendance.svg` |
| Contracts / Leaves / Overtime | `svg/erd-04-contracts-leave-ot.svg` |
| Performance / Rewards / Reports | `svg/erd-05-performance-rewards-reports.svg` |

## Class Diagram
| Section | File |
|---|---|
| Class diagram tổng thể (20 model) | `svg/class-diagram-01.svg` |

## Use Case (`use_cases.md`)
`svg/use-cases-02.svg` … `svg/use-cases-11.svg` (từng nhóm chức năng). *(01 = tổng quát: bỏ ảnh, để bảng.)*

## Activity Diagrams (`activity_diagrams.md`) — per-function
`svg/activity-diagrams-01.svg` … `-58.svg` — 1 hình / chức năng, theo thứ tự 1.1 → 10.6 (bỏ 10.5).
Thứ tự: 01-07 Tài khoản (1.1-1.7) · 08-13 Hồ sơ (2.1-2.6) · 14-19 Hợp đồng (3.1-3.6) ·
20-28 Chấm công (4.1-4.9) · 29-34 Nghỉ phép (5.1-5.6) · 35-39 Tăng ca (6.1-6.5) ·
40-43 Đánh giá (7.1-7.4) · 44-49 Thưởng/phạt (8.1-8.6) · 50-53 Báo cáo/Ticket (9.1-9.4) ·
54-58 Thống kê/Cài đặt (10.1-10.4, 10.6). Map đầy đủ: `COVERAGE.md`.

## State Diagrams (`state_diagrams.md`)
`svg/state-diagrams-01.svg` … `-08.svg` — vòng đời entity (gộp entity giống nhau).
01 ST-CONTRACT · 02 ST-FACECHANGE · 03 ST-ADJUST · 04 ST-APPROVAL2 (nghỉ phép + tăng ca) ·
05 ST-EVAL · 06 ST-REWARD · 07 ST-REPORT · 08 ST-TICKET.

## Data Flow Diagram (`data_flow_diagram.md`)
`svg/data-flow-diagram-01.svg`, `-03.svg` … `-06.svg`
01 Context L0 · *(02 Phân rã L1: bỏ ảnh, để bảng — quá rộng)* · 03 L2 Xác thực · 04 L2 Chấm công · 05 L2 Duyệt 2 bước · 06 L2 Thống kê.

## Code Flow (`code_flow.md`) — sequence/state
`svg/code-flow-01.svg` … `-15.svg`
01 Đăng ký · 02 Đăng nhập · 03 Quên MK · 04 Duyệt 2 bước · 05 Đăng ký khuôn mặt ·
06 Nhận diện+chấm công · 07 HĐ versioning · 08 Lịch sử HĐ · 09 Báo cáo (state) · 10 Ticket (state) ·
11 Đánh giá · 12 Thống kê · 13 Notification · 14 Face change anti-fraud · 15 Cảnh báo HĐ hết hạn.

## Sequence Diagrams (`sequence_diagrams.md`) — per-function
`svg/sequence-diagrams-01.svg` … `-58.svg` — 1 hình / chức năng, cùng thứ tự & numbering với Activity ở trên.

## Deployment & How-it-works
| Section | File |
|---|---|
| Kiến trúc deploy Render | `svg/deployment-architecture-01.svg` |
| Vòng đời request (how it works) | `svg/how-it-works-01.svg` |

---

## Lệnh render (tham khảo)

```bash
cd docs/diagrams
export PUPPETEER_SKIP_DOWNLOAD=1   # dùng Chrome có sẵn (xem puppeteer.config.json)
python extract.py                  # tách block ```mermaid từ *.md -> src/*.mmd
for f in src/*.mmd; do
  b=$(basename "$f" .mmd)
  # bỏ 3 sơ đồ tổng quan quá khổ (để dạng bảng/văn bản trong báo cáo)
  case "$b" in use-cases-01|data-flow-diagram-02) continue;; esac
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "svg/$b.svg" \
    -b white -c mermaid.config.json -p puppeteer.config.json
done
```

> Sửa nội dung sơ đồ ở file `.md` gốc (không sửa `src/*.mmd` — bị `extract.py` ghi đè).
> Sơ đồ ERD module (`erd-*.mmd`) viết tay trong `src/`, không qua extract.
