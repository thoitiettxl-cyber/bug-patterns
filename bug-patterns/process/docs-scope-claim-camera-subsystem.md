# Docs khẳng định sai scope hooks (D-P0-1)

- **Triệu chứng:** `HOOK_MAP.md` khẳng định "Every hook is installed from
  HookModuleRegistry.kt" trong khi camera subsystem cài qua entry point riêng.
  (SpoofX, audit 2026-10-05.)
- **Root cause:** Camera2Magic port thêm `installCameraSubsystem` trong
  `SpoofXModule` sau khi docs scope được viết; docs không được update theo.
- **Fix:** Sửa claim + document camera subsystem (entry point, thứ tự cài đúng:
  `hookApplicationOnCreate()` trước rồi mới `Camera1/2Hooker`,
  `ImageReaderHooker`, `WebRTCHooker`; `libcamera3.so`) vào `HOOK_MAP.md` +
  `ARCHITECTURE.md`. KHÔNG refactor code.
- **Check:** grep mọi entry point cài hook trong code (`installCameraSubsystem`,
  `HookModuleRegistry`) — tất cả đều có mặt trong docs, thứ tự khớp code.
