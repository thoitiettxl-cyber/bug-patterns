# ĐÍNH CHÍNH (2026-10-02): 4 "API miuix chưa release" thực ra là FILE LOCAL của template

**Kết luận cũ trong file này là SAI và đã được đính chính.** Giữ lại nội
dung gốc bên dưới làm bài học về "verify không tới nơi", nhưng root cause
đúng như sau:

- 4 symbol `rememberCombinedBackdrop`, `BackdropEffectScope.vibrancy()`,
  `BackdropEffectScope.lens()`, `Modifier.innerShadow` **là code local
  của template Camera2Magit**, 4 file cùng package
  `com.nothing.camera2magic.ui.component.liquid`:
  `CombinedBackdrop.kt:45`, `Vibrancy.kt:12`, `Lens.kt:22`,
  `InnerShadow.kt:48` (verify trực tiếp 2026-10-02).
- Template khai báo **đúng miuix 0.9.4-rc01** — khớp 100% version SpoofX
  đang dùng. Không có chuyện "API chưa release".
- Lỗi CI `36898698969` không phải do API thiếu trong library, mà do lúc
  copy M1 chỉ copy `LiquidGlassNavigationBar.kt` mà **quên copy 4 file
  companion** cùng package. Giả thuyết "FROM-CACHE che lỗi" là suy diễn
  thiếu verify — bài học: khi copy thiếu file, đừng vội kết luận về
  library, hãy `find` cả package nguồn trước.
- Fix đúng: port 4 file local sang `com.thoittxl.spoofx.ui.component.liquid`
  (đổi package, giữ header SPDX), rồi adapt NavigationBar dùng API thật.

---

# (Nội dung gốc — giữ làm bài học)

# Copy file từ miuix upstream/example gọi API liquid-glass chưa release (`rememberCombinedBackdrop`, `lens()`, `vibrancy()`, `innerShadow`)

- **Triệu chứng:** `compileDebugKotlin` fail với 9 lỗi `Unresolved
  reference` tại `LiquidGlassNavigationBar.kt` — các symbol
  `rememberCombinedBackdrop`, `BackdropEffectScope.vibrancy()`,
  `BackdropEffectScope.lens()`, `Modifier.innerShadow`/`InnerShadow` — dù
  file được copy 1:1 từ template (Camera2Magit dev-next @ `2195798`)
  vốn "CI xanh". (SpoofX, 2026-10-02, CI run `36898698969`.)
- **Root cause (SAI — xem đính chính trên):** 4 API trên là "liquid glass" từ
  **miuix upstream chưa release** — không tồn tại trong BẤT KỲ bản release nào...
- **Fix đã áp dụng (fallback, nay đã lỗi thời khi port đủ file):** xem git log
  dev-codex — các comment `// Fallback:` trong `LiquidGlassNavigationBar.kt`
  sẽ được thay bằng API thật khi port 4 file companion.
- **Phòng (check chạy được — vẫn đúng):**
  ```bash
  # trước khi copy file từ repo khác dùng symbol lạ:
  # 1. find cả package nguồn xem symbol là local hay library:
  find <repo-nguon> -path "*ui/component/liquid*" -name "*.kt"
  # 2. grep định nghĩa symbol trong repo nguồn:
  grep -rn "fun rememberCombinedBackdrop" <repo-nguon>/app/src
  # 3. rồi mới kết luận về library (sources.jar) hay thiếu file
  ```
  Luật: **copy file từ repo khác → liệt kê cả package nguồn trước,
  đừng copy 1 file rồi suy diễn về library khi thiếu symbol.**
