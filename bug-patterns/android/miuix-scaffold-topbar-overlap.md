# Miuix Scaffold đặt content ở y=0 DƯỚI top bar — bỏ `calculateTopPadding()` là content bị bar che

- **Triệu chứng:** Tab Cài đặt: mục đầu tiên ("Ngôn ngữ") bị che sau
  app bar, user phải kéo-xuống overscroll mới thấy. Tab Profiles: header
  cố định (StatsRow + SearchBar) cũng bắt đầu từ y=0, đè dưới bar.
  Chỉ hiện khi `innerPadding` của Scaffold chỉ dùng
  `calculateBottomPadding()` mà không cộng `calculateTopPadding()`.
  (SpoofX `MainScreen.kt` `TabHost`, 2026-10-01 — report audit layout,
  root cause verify bằng source miuix `0.9.4-rc01`.)

- **Root cause:** Miuix `Scaffold` KHÔNG offset content xuống dưới top bar
  (khác contract mặc định của Material3 `Scaffold` mà dev thường assume).
  Nó đặt content ở y=0 — cùng vùng với app bar. Contract: content phải tự
  apply `padding.calculateTopPadding()` (bằng chiều cao bar hiện tại, tự
  co lại khi bar collapse với `MiuixScrollBehavior`). Chỉ lấy
  `calculateBottomPadding()` → toàn bộ content bắt đầu từ y=0, bị che sau
  bar.

- **Fix:** Trong content lambda của Scaffold:
  ```kotlin
  val bottomPadding = padding.calculateBottomPadding()
  val topPadding = padding.calculateTopPadding()
  ```
  Truyền `topPadding` xuống các screen (param `topPadding: Dp = 0.dp`
  để không gãy call site khác). Ở mỗi screen:
  - `LazyColumn` thường: `contentPadding = PaddingValues(
      top = 12.dp + topPadding, bottom = bottomPadding)` — giữ nguyên
      padding có sẵn, chỉ cộng thêm.
  - Screen có header cố định (Column + LazyColumn weight): cộng
    `topPadding` vào root `Column` (`.padding(top = topPadding)`) —
    header cố định cũng phải bắt đầu dưới bar, không phải chỉ list.
  KHÔNG đụng `TopAppBarState` shared reset (P1, chờ quyết định riêng).

- **Phòng (check chạy được):**
  ```bash
  # Mọi Scaffold có topBar trong module UI: content lambda phải dùng
  # calculateTopPadding() — chỗ nào chỉ có calculateBottomPadding() là
  # nghi ngờ bị che sau bar.
  grep -rn "calculateBottomPadding()" lsmodule/src/main/java --include="*.kt" \
    | while IFS= read -r line; do
        f="${line%%:*}"
        grep -q "calculateTopPadding()" "$f" \
          || echo "MISSING TOP PADDING: $line"
      done
  # Trường hợp ngoại lệ hợp lệ: screen không có topBar (editor,
  # dialog) — xác nhận bằng mắt, không auto-fix.
  ```
  Luật: **Miuix Scaffold + có `topBar` → content BẮT BUỘC cộng
  `calculateTopPadding()` vào top. Đừng assume Scaffold tự đẩy
  content xuống (contract khác Material3).**

- **Nguồn:** SpoofX `MainScreen.kt`/`ProfilesScreen.kt`/
  `AppsScreen.kt`/`SettingsScreen.kt`, fix P0 2026-10-01 (nhánh
  `dev-codex`), contract từ source miuix-kmp `0.9.4-rc01`.
