# launcher-tap-new-activity-standard-resets-nav

## Triệu chứng
Đang ở tab Scope/Settings (hoặc trang con) → sang app khác → tap icon launcher
quay lại → app luôn nhảy về Home (mất nav state). Bấm Back còn "lòi" ra state
cũ bên dưới.

## Root cause
`MainActivity` dùng `launchMode` mặc định (`standard`), không phải code reset
nav, không phải lỗi backstack-saver. Launcher gửi `ACTION_MAIN` +
`CATEGORY_LAUNCHER` + `FLAG_ACTIVITY_NEW_TASK`; với `standard`, hệ thống tạo
**instance activity mới** trên cùng task, `savedInstanceState = null` →
Compose build lại từ seed (`rememberSpoofXBackStack(Main)`) → luôn về Home.
Activity cũ còn nằm dưới trong task → Back hiện lại state cũ (đúng triệu chứng).

## Fix
Một dòng trong `AndroidManifest.xml`:

```xml
<activity
    android:name=".MainActivity"
    android:exported="true"
    android:launchMode="singleTask">
```

`singleTask` → tap icon bring task cũ lên foreground (gọi `onNewIntent`,
không cần implement gì thêm), không tạo instance mới → giữ nguyên tab +
back stack.

## Check phòng ngừa
```bash
# Launcher activity nào thiếu launchMode thì kiểm tra hành vi tap-icon:
rg -n -A4 'android:name=".MainActivity"' lsmodule/src/main/AndroidManifest.xml
# Lưu ý: đường Recents-resume sau OS kill process vẫn phụ thuộc
# rememberSaveable restore — đó là degrade an toàn có chủ ý, không phải bug.
```
