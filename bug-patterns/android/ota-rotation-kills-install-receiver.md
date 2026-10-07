# Xoay màn hình giữa OTA Installing → receiver mất, treo câm (U-P1-1)

- **Triệu chứng:** Xoay màn hình khi OTA đang `Installing` → UI về `Idle`, dialog
  confirm cài đặt của hệ thống không bao giờ hiện, session PackageInstaller đã
  commit treo câm (không broadcast nào được xử lý nữa). (SpoofX, audit 2026-10-05.)
- **Root cause:** `statusReceiver` đăng ký trên application context nhưng bị
  unregister trong `DisposableEffect.onDispose` — mà dispose chạy cả khi rotation
  (composition dispose ≠ màn hình đóng). Composition mới về `Idle` và mất
  `pendingInstallSessionId`; broadcast `STATUS_PENDING_USER_ACTION` /
  `STATUS_SUCCESS` không còn listener.
- **Fix:** Hoist receiver + `pendingInstallSessionId` + `installAttemptId` +
  watchdog vào `UpdateViewModel` (ViewModelStore của nav entry sống qua rotation);
  bỏ `DisposableEffect` unregister; teardown chỉ trên terminal status,
  watchdog-timeout fallback, và `onCleared()` (pop thật).
- **Check chạy được:** (1) `preflight-edit check` pass; (2) máy thật + nightly CI:
  vào UpdateScreen → Download → Install → xoay giữa `Installing` → phải thấy
  spinner `Installing` (không về `Idle`), dialog confirm hệ thống hiện, sau
  confirm báo `InstallSuccess`; (3) xoay giữa `WaitingSystemConfirm` → dialog
  hệ thống vẫn xử lý được; (4) back giữa `Installing` → `onCleared` abandon
  session (logcat `abandonSession`).
