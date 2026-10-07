# Android Location: speed accuracy API là `...MetersPerSecond`, không phải `...Meters`

- **Triệu chứng:** `:lsmodule:compileDebugKotlin` fail
  `Unresolved reference 'speedAccuracyMeters'` ở `FakeGpsModule.kt`
  (SpoofX, 2026-10-03, campaign location-spoof-anti-mock). Lỗi lọt qua
  writer + 2 vòng review fresh-eyes — cả 3 đều "nhớ" tên API sai.
- **Root cause:** họ API accuracy của `android.location.Location` (API 26+)
  đặt tên KHÔNG đối xứng:
  - `getVerticalAccuracyMeters()` / `setVerticalAccuracyMeters(float)` ✓
  - `getBearingAccuracyDegrees()` / `setBearingAccuracyDegrees(float)` ✓
  - `getSpeedAccuracyMetersPerSecond()` /
    `setSpeedAccuracyMetersPerSecond(float)` ← có hậu tố `PerSecond`
  Viết `getSpeedAccuracyMeters` / `setSpeedAccuracyMeters` (bỏ `PerSecond`)
  thì compile fail (property Kotlin `speedAccuracyMetersPerSecond` map đúng
  sang setter thật). Hook reflective (`overrideFloat(cls, "getSpeedAccuracyMeters")`)
  thì compile qua nhưng runtime lookup miss → skip lặng lẽ (P3/L8) → feature
  chết lâm sàng không ai hay.
- **Fix:** dùng đúng tên `getSpeedAccuracyMetersPerSecond` /
  `setSpeedAccuracyMetersPerSecond` (property Kotlin:
  `speedAccuracyMetersPerSecond`). Đã verify qua docs (Microsoft Learn
  mirror Android API 34/35: `SpeedAccuracyMetersPerSecond`).
- **Phòng (check chạy được):**
  ```bash
  # Khi đụng họ Location accuracy API, verify tên method qua AOSP source
  # (android.googlesource.com, location/java/android/location/Location.java)
  # hoặc Context7 — KHÔNG tin trí nhớ, kể cả khi 2/3 tên còn lại "đúng pattern".
  # Đặc biệt: reflective hook phải có unit test assert lookup thành công
  # (fail loud) thay vì skip lặng lẽ.
  ```
