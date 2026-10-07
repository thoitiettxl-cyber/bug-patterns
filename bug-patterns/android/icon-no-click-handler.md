# Icon trông như nút bấm nhưng không có click handler

- **Triệu chứng:** icon Pin trên mỗi row hồ sơ (hiện khi profile được ghim)
  trông như nút toggle nhưng bấm vào không có phản hồi gì; muốn ghim/bỏ
  ghim phải mở menu ⋯. (SpoofX, 2026-10-01, `ProfilesScreen.kt` — `Icon`
  trần đặt cạnh `IconButton` của menu nên càng dễ nhầm là bấm được.)
- **Root cause:** icon chỉ là indicator trạng thái (`if (profile.pinned)
  Icon(...)`), không ai wire `onClick`. Dạng "nút chết" khó phát hiện bằng
  compile/lint vì code hoàn toàn hợp lệ.
- **Fix (SpoofX `cf7c8f8`):** thêm param `onPin: () -> Unit` vào `ProfileRow`,
  call-site truyền `onPin = { togglePin(profile) }` (dùng lại đúng hàm của
  menu), bọc icon trong `IconButton(onClick = onPin)`. Không default param
  → compiler bắt buộc mọi call-site phải truyền, không sót.
- **Phòng (check chạy được):**
  ```bash
  # icon đứng một mình (không trong IconButton/clickable) mà trông như control:
  grep -rn -B2 -A6 "MiuixIcons\." --include=*.kt lsmodule/src/main/java/com/thoittxl/spoofx/ui | grep -A6 "Icon(" | grep -v "IconButton" | head -20
  ```
  Quy tắc: mọi `Icon` đặt cạnh các control tương tác được phải tự trả lời —
  hoặc là indicator thuần (đặt chỗ không gây nhầm), hoặc bọc
  `IconButton`/`clickable`. Sweep UI phải tap thử từng icon.
