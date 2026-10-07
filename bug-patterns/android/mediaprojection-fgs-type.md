# MediaProjection chỉ tạo được trong FGS type mediaProjection (Android 14+)

- **Triệu chứng:** `getMediaProjection()` trả null / throw trên Android 14+
  dù user đã grant.
- **Root cause:** Từ Android 14, MediaProjection chỉ được tạo khi đang có
  foreground service đúng type `mediaProjection` chạy.
- **Fix (E-Muse):** không consume grant ở activity; chuyển resultCode + data
  sang service (`ACTION_START_PROJECTION`), service add type
  `FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION` rồi mới `getMediaProjection`.
  Manifest khai báo `foregroundServiceType="...|mediaProjection"`.
- **Phòng:** feature nào cần screenshot/MediaProjection → thiết kế service
  nhận grant ngay từ đầu, đừng để activity giữ.
- **Nguồn:** E-Muse `MuseService.startProjection`.
