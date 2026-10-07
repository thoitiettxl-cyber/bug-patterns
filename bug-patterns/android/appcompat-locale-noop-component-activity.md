# appcompat-setapplicationlocales-noop-component-activity

## Triệu chứng
Settings → chọn Ngôn ngữ: bấm chọn xong `recreate()` nhưng app giữ nguyên ngôn
ngữ. Lựa chọn cũng không persist (kill app mở lại mất, pill chọn nhảy về
"Theo hệ thống").

## Root cause
`AppCompatDelegate.setApplicationLocales()` chỉ apply qua các *active delegate*
— mỗi `AppCompatActivity` tạo một delegate; static setter gọi
`applyLocalesToActiveDelegates()`. `MainActivity` là `ComponentActivity`
(không phải AppCompatActivity) → không bao giờ tạo delegate → tập active
delegates rỗng → call **silent no-op**: chỉ cập nhật static nội bộ của AppCompat,
không wrap context nào. `recreate()` thủ công dựng lại activity với đúng
configuration cũ → stringResource không đổi.

Xác nhận độc lập: project zioalex/getinspiredbythebible (commit de5d7de)
document đúng bug này.

## Fix
`minSdk >= 33` → bỏ AppCompat, gọi thẳng framework (tự persist, tự recreate):

```kotlin
val lm = appContext.getSystemService(LocaleManager::class.java)
lm.applicationLocales = if (tags.isEmpty()) LocaleList.getEmptyLocaleList()
                        else LocaleList.forLanguageTags(tags)
```

Lưu ý: `LocaleList.getEmpty()` KHÔNG tồn tại trong SDK — factory đúng là
`getEmptyLocaleList()` (verify bằng `javap` trên android.jar, đừng tin trí nhớ).

## Check phòng ngừa
```bash
# App dùng ComponentActivity mà còn gọi AppCompatDelegate.* thì nghi ngờ:
rg -n "AppCompatDelegate" lsmodule/src/main/java
# Mọi claim "API X tồn tại" phải verify qua javap/source-jar/Context7.
```
