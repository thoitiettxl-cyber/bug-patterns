# sdkmanager: package platform API 37+ phải ghi android-37.0

- **Triệu chứng:** CI fail ở bước cài SDK: `Warning: Failed to find package
  'platforms;android-37'` → exit code 1. (tami-stealth, 2026-10-04.)
- **Root cause:** Từ API 37 Google đổi quy ước tên package platform thành
  `platforms;android-37.0` (có minor `.0`, kiểu như `android-8.1` ngày xưa).
  `platforms;android-37` (không minor) KHÔNG tồn tại. Từ API 36 trở xuống
  vẫn dùng tên cũ (`platforms;android-36`).
- **Fix:** dùng `"platforms;android-37.0"` trong lệnh sdkmanager.
  (Recipe đã verify: E-Muse `release.yml` cài
  `"platforms;android-37.0" "build-tools;37.0.0"` CI xanh ngày 2026-09-30.)
- **Phòng:** khi bump compileSdk lên API mới, kiểm tra tên package thật
  trong `sdkmanager --list` (hoặc copy recipe từ repo đã build xanh),
  đừng đoán theo pattern API cũ.
- **Nguồn:** tami-stealth `nightly.yml` run `37205219048`.
