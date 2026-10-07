# Legacy prefs key và key mới cùng điều khiển theme → xung đột mỗi cold start

- **Triệu chứng:** user đổi theme trong màn settings mới (Miuix/Compose) nhưng
  sau khi kill app mở lại, theme nhảy về giá trị cũ; hoặc Compose theme và
  AppCompatDelegate nói 2 đằng khác nhau. (SpoofX, 2026-10-02:
  `SpoofXApplication.onCreate` apply legacy `theme_mode` qua
  `AppCompatDelegate.setDefaultNightMode`, trong khi Compose theme đọc key
  mới `theme_dark_mode` từ `readThemeConfig()`.)
- **Root cause:** 2 nguồn truth. Key cũ (`theme_mode`, int MODE_NIGHT_*)
  tồn tại từ trước template-port; key mới (`theme_dark_mode`, colorMode
  0/1/2) do `writeThemeConfig()` ghi. Application luôn apply key cũ mỗi
  cold start nên thắng ngay cả khi user đã migrate sang settings mới.
- **Fix (migration-aware, minimal):** trong `Application.onCreate`, chỉ apply
  legacy key khi key mới CHƯA tồn tại (`prefs.contains(KEY_THEME_DARK_MODE)`);
  một khi key mới có mặt thì nó thắng ở mọi nơi. Không đổi semantics của
  ThemeSettings/`readThemeConfig()` (migration một chiều giữ nguyên).
- **Phòng (check chạy được):**
  `rg "setDefaultNightMode" lsmodule/src/main/java --type kotlin` — mọi
  call site phải đi kèm guard `contains(<new key>)`; thêm prefs key mới thì
  grep xem key cũ cùng domain có còn được apply ở Application không.
