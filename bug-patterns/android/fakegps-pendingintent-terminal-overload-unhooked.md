# FakeGps: overload PendingIntent terminal chưa hook → lộ location thật

- **Triệu chứng:** Bật `fake_gps`, app dùng
  `LocationManager.requestLocationUpdates(String, LocationRequest, PendingIntent)`
  (geofencing, background tracking) vẫn nhận location thật. (SpoofX, audit 2026-10-05.)
- **Root cause:** Chỉ hook terminal overload listener
  `(String, LocationRequest, Executor, LocationListener)`. Trên AOSP, overload PI
  là terminal độc lập gọi thẳng `mService.registerLocationPendingIntent(...)`,
  không funnel qua listener terminal đã hook → real location leak.
- **Fix:** Hook thêm overload `(String, LocationRequest, PendingIntent)` (API 31+),
  swallow subscription, deliver fake `Location` qua `PendingIntent.send` với extra
  `KEY_LOCATION_CHANGED` theo đúng schedule discipline (interval/minDistance/
  expiry/maxUpdates, WeakReference PI, self-retire); hook `removeUpdates(PendingIntent)`
  để cancel stream.
- **Check chạy được:** máy thật + nightly CI: bật fake_gps, app test gọi PI overload
  → logcat thấy fake coords trong Intent extra; `removeUpdates(PI)` → stream dừng;
  empty profile → real method chạy.
