# `AppCompatDelegate.setDefaultNightMode()` là no-op trên `ComponentActivity`

- **Triệu chứng:** nút Sáng/Tối/Theo hệ thống bấm không đổi giao diện gì.
  Pref vẫn được ghi vào `settings_prefs` (`theme_mode` int) và segmented
  control vẫn hiện đúng trạng thái đã chọn (local state update) — nhưng
  theme của app không đổi. (SpoofX, 2026-10-01, `MainActivity` extends
  `ComponentActivity`, UI Compose + Miuix, theme qua `ThemeConfig`.)
- **Root cause:** `AppCompatDelegate.setDefaultNightMode()` chỉ có tác dụng
  với `AppCompatActivity` / `AppCompatDelegate`-hosted activity. `MainActivity`
  là `ComponentActivity` (androidx.activity) — không qua AppCompat pipeline —
  nên call này là no-op hoàn toàn. Đồng thời `MainActivity.setContent` gọi
  `SpoofXTheme {` với `ThemeConfig` mặc định (`colorMode = 0`) và không bao
  giờ đọc `theme_mode` từ prefs → UI (ghi prefs) và logic render (theme
  composable) hai đường không nối nhau. Vì không có exception hay log nào,
  bug này dễ bị nhầm là "wiring vào ThemeConfig là later batch" (KDoc cũ)
  trong khi thực chất đường `setDefaultNightMode` không bao giờ làm việc.
- **Fix:**
  1. `MainActivity.setContent`: đọc prefs (`UiPrefs.PREFS_NAME` /
     `KEY_THEME_MODE`) thành state, map
     `MODE_NIGHT_NO → colorMode 1` (light), `MODE_NIGHT_YES → 2` (dark),
     `else → 0` (follow system), rồi truyền
     `SpoofXTheme(themeConfig = ThemeConfig(colorMode = colorMode))`.
     `SpoofXTheme` dùng `themeConfig.resolveIsDark(systemDark)` nên chỉ cần
     truyền `colorMode` là đủ — không cần sửa `Theme.kt`/`ThemeConfig.kt`.
  2. `SettingsScreen.setTheme`: XÓA `AppCompatDelegate.setDefaultNightMode(mode)`
     (no-op), GIỮ `prefs.edit().putInt(...)`, THÊM
     `context.findActivity()?.recreate()` — mẫu có sẵn ở `setLanguage` —
     để activity recreate và `MainActivity` đọc lại prefs ở lần compose mới.
  3. Cập nhật KDoc mô tả theme đúng luồng mới; `AppCompatDelegate` vẫn dùng
     cho locale (`getApplicationLocales`/`setApplicationLocales`) và các
     constant `MODE_NIGHT_*` → giữ import.
- **Phòng (check chạy được):**
  ```bash
  # activity base class không phải AppCompatActivity thì không được gọi API này:
  grep -rn "setDefaultNightMode" --include=*.kt lsmodule/src/main  # phải trắng
  # verify mapping mode -> colorMode đúng semantics ThemeConfig (0/1/2):
  grep -n "colorMode = when" lsmodule/src/main/java/com/thoittxl/spoofx/MainActivity.kt
  ```
  Quy tắc: trên `ComponentActivity`, theme phải đi qua state trong `setContent`
  (prefs + `recreate()` khi đổi), không qua AppCompat global delegate.
  Mọi call `AppCompatDelegate.setDefaultNightMode` không ở `AppCompatActivity`
  đều phải bị nghi ngờ — grep và xóa.

## Lesson phụ (2026-10-01, trong cùng lần fix)
`SpoofXApplication.onCreate()` cũng gọi `setDefaultNightMode` ("early theme
re-apply") — cùng một class no-op với `ComponentActivity`, nhưng nằm ngoài
phạm vi batch fix UI này (thuộc Application layer). Dead code vô hại, không
gây regression; cần một pass dọn riêng, không lẫn vào writer contract.
