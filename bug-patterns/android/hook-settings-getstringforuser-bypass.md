# Bug pattern: `Settings` mask bypass qua `getStringForUser`

## Triệu chứng
Module mask `android_id` (hoặc bất kỳ key `Settings.*` nào) bằng cách hook
các method tên `getString`, nhưng detector gọi trực tiếp
`Settings.Secure.getStringForUser(cr, "android_id", userId)` — hoặc
reflection vào `Settings$NameValueCache.getStringForUser` — và thấy giá trị
thật. Không có crash, không có log lỗi; mask bị lách trong im lặng.

## Root cause
Filter `m.name != "getString"` bỏ qua mọi overload khác có cùng signature
trả về key:
- `Settings.Secure.getStringForUser(ContentResolver, String, int)` — public
  API tĩnh, detector biết và gọi trực tiếp.
- `Settings.NameValueCache.getStringForUser(ContentResolver, String, int)` —
  cache nội bộ mà mọi `Settings.*#get*` public đều delegate xuống; callers
  dùng reflection đi đường tắt qua đây.

## Fix
Mở rộng filter thành `m.name != "getString" && m.name != "getStringForUser"`,
và hook cả inner cache class `android.provider.Settings$NameValueCache`.
Lưu ý: trên `getStringForUser` thì **key ở arg index 1**, không phải
`args.lastOrNull()` (arg cuối là `userId`). Mẫu đã được chứng minh trong
`DevOptionsHideModule.kt` (hook `Settings.Global`/`Settings.Secure` +
`NameValueCache`) và `DeviceIdHideModule.hookAndroidId`.

## Check grep phòng ngừa
```bash
# Module nào hook getString mà thiếu getStringForUser:
rg -l 'm.name != "getString"' lsmodule/src/main/java/com/thoittxl/spoofx/hooks/
# → kiểm tra từng file: nếu module mask key Settings.* thì phải cover cả
# getStringForUser trên chính class Settings.* đó + NameValueCache.
```

## Ví dụ trong repo
- `DeviceIdHideModule.kt::hookAndroidId` — fix 2026-10-02 (batch 3, bug 1)
- `DevOptionsHideModule.kt` — pattern chuẩn (getString + NameValueCache)
