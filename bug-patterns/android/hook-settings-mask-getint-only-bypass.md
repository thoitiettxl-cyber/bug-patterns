# Bug pattern: `Settings` int-mask bị bypass qua `getString` + parseInt

## Triệu chứng
Module mask key `Settings.*` bằng `SettingsIntMask.mask(...)` (chỉ hook 2
overload `getInt`), nhưng detector đọc
`Settings.Global.getString(cr, "airplane_mode_on")` rồi `Integer.parseInt` —
thấy giá trị thật (1) trong khi `getInt` trả 0. Mask không giữ được nhất
quán giữa các entry point.

## Root cause
`SettingsIntMask.mask` chỉ cài hook trên `getInt(ContentResolver, String)`
và `getInt(ContentResolver, String, int)`. AOSP `getInt` nội bộ gọi
`getString` + parse, nhưng detector không bắt buộc phải đi qua `getInt`
public — gọi `getString` trực tiếp là hoàn toàn hợp lệ, hoặc đi tắt qua
`Settings$NameValueCache.getStringForUser` bằng reflection.

## Fix
Bổ sung hook `getString` cho đúng key đó trên các namespace `Settings.*`
tương ứng, trả về giá trị mask dạng string (cùng giá trị số mà `getInt`
mask đang trả, `"0"`), và cover thêm `getStringForUser` của
`Settings.NameValueCache`. Mẫu đã được chứng minh trong
`DevOptionsHideModule.kt` (hookGetString + hookNameValueCache) và áp dụng
cho `AirplaneModeHideModule`.

## Check grep phòng ngừa
```bash
# Module nào dùng SettingsIntMask.mask mà không có hook getString cho cùng key:
rg -n 'SettingsIntMask\.mask' lsmodule/src/main/java/com/thoittxl/spoofx/hooks/*.kt
# → với mỗi module, kiểm tra: có hookGetString cho cùng key trên cùng
# namespace không? Có NameValueCache#getStringForUser không?
```

## Ví dụ trong repo
- `AirplaneModeHideModule.kt` — fix 2026-10-02 (batch 3, bug 3)
- `DevOptionsHideModule.kt` — pattern chuẩn (getInt + getString + NameValueCache)
