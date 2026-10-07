# Crash khi save state: `Double.NaN`/`Infinity` lọt vào route được `Json.encodeToString` trong `Saver.save`

- **Triệu chứng:** app crash với `kotlinx.serialization.json.JsonEncodingException`
  (subclass của `IllegalArgumentException`):
  `Unexpected special floating-point value NaN...` — ném từ
  `Activity.onSaveInstanceState` → `SaveableStateRegistry.performSave()`,
  không có try/catch nào trên đường đi. Crash chỉ xảy ra khi xoay màn hình /
  background app trong lúc route "độc" còn trên back stack; mở màn hình đó
  bình thường trông không có gì sai. (SpoofX, 2026-10-01: user gõ `NaN` vào
  ô FAKE_LAT ở tab Vị trí → route `LocationPicker(NaN, …)`.)
- **Root cause:** hai lớp.
  1. `"NaN".toDoubleOrNull()` trả về `Double.NaN` — Java `parseDouble` chấp
     nhận `NaN`/`Infinity`/`1e309`(→`+Infinity`) mà không báo lỗi, nên text
     field "hợp lệ" vẫn đẩy được giá trị non-finite vào route.
  2. `kotlinx.serialization.json` mặc định CẤM số non-finite (không đúng JSON
     spec). Chiều `decode` của Saver đã bọc `runCatching` ("never crash on
     restore") nhưng chiều `encode` (`Saver.save`) thì không — một asymmetric
     guard để sót.
- **Fix (2 lớp, SpoofX `a39eaf0`):**
  1. Tại push site (`LocationScreen.kt`): normalize ngay khi tạo route —
     `lat.toDoubleOrNull()?.takeIf { it.isFinite() }`. `null` → picker
     fallback về mặc định như cũ, hiển thị không đổi.
  2. Defense in depth trong `NavBackStackSaver.encodeBackStack()`: bọc
     `encodeToString` bằng `runCatching`, fail thì `Log.w` + fallback encode
     `listOf(SpoofXRoute.Profiles)` (payload hard-coded an toàn, không user
     data; nếu chính fallback throw thì exception vẫn propagate, không nuốt
     vòng lặp) — đối xứng với `decodeBackStack`.
- **Phòng (check chạy được):**
  ```bash
  # mọi toDoubleOrNull() đi vào @Serializable route phải qua isFinite():
  grep -rn "toDoubleOrNull()" --include=*.kt lsmodule/src/main | grep -v "isFinite"
  # Saver.save và Saver.restore phải đối xứng guard:
  grep -n "runCatching" lsmodule/src/main/java/com/thoittxl/spoofx/ui/navigation/NavBackStackSaver.kt  # phải có 2
  ```
  Quy tắc: bất kỳ `Double` nào đi vào `@Serializable` class dùng với
  `Json.encodeToString` đều phải qua `takeIf { it.isFinite() }` (hoặc bật
  `allowSpecialFloatingPointValues` một cách có chủ ý). `Saver.save` và
  `restore` luôn guard đối xứng nhau.
