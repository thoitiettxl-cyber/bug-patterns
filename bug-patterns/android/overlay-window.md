# Overlay window: sai context + nuốt exception

- **Triệu chứng:** Toggle "Bóng nổi" bật nhưng bubble không hiện, log không
  chạy, không có lỗi nào trong logcat. (E-Muse, 2026-09-29.)
- **Root cause (2 lỗi):**
  1. `TYPE_ACCESSIBILITY_OVERLAY` chỉ add được từ **context của chính
     accessibility service** (service sở hữu window token). Add từ app/activity
     context bị WMS reject bằng `BadTokenException` dù instance != null.
     (Pattern đúng học từ Eta `GestureIndicator.kt`: resolve service trước,
     dùng nó làm overlay context cho cả WindowManager lẫn view.)
  2. `runCatching` nuốt luôn throw → toggle bật nhưng bubble/log chết lặng,
     không ai biết vì sao.
- **Fix (E-Muse `9899652`):** dùng `MuseAccessibilityService.instance` làm
  overlay context (fallback `TYPE_APPLICATION_OVERLAY` khi service chưa
  connect và có `canDrawOverlays`); chỉ set state sau `addView` success;
  log lỗi thay vì nuốt.
- **Phòng (check chạy được):**
  ```bash
  # cấm runCatching/try-catch không log ở critical path overlay/service
  grep -rn "runCatching" --include="*.kt" app/src | grep -v "onFailure" | grep -v "getOrNull\|getOrDefault"
  # rà từng kết quả: chỗ nào nuốt exception của addView/removeView/startForeground là bug
  ```
  Luật: **critical path (service lifecycle, addView, tunnel) không được nuốt
  exception — log hoặc fail loudly.**
- **Nguồn:** E-Muse commit `9899652`, 2026-09-29.
