# Explicit Intent + dynamic BroadcastReceiver → broadcast rơi thầm lặng

## Triệu chứng
- `PackageInstaller.Session.commit()` thành công (logcat: `committed install session 744549522`).
- Broadcast trạng thái (SUCCESS / PENDING_USER_ACTION / FAILURE) **không bao giờ** tới `onReceive`.
- UI treo vĩnh viễn ở trạng thái chờ ("Preparing the install session..."), không crash, không log lỗi — vì broadcast drop là silent.

## Root cause
- Status `Intent` nhúng trong `PendingIntent.getBroadcast()` được build **explicit**: `Intent(context, ReceiverClass::class.java)` (có `component`).
- Receiver chỉ đăng ký động qua `registerReceiver(receiver, IntentFilter(action), RECEIVER_NOT_EXPORTED)` — **không có trong AndroidManifest**.
- Trong `ActivityManagerService.broadcastIntentLocked()`, tập dynamic receiver (`mReceiverResolver.queryIntent()`) **chỉ được query khi `intent.getComponent() == null`**; intent explicit được resolve duy nhất qua manifest (`PackageManager.getReceiverInfo(component)`) → component không tồn tại trong manifest → broadcast tới không ai, rơi thầm lặng.
- Nguồn: AOSP `broadcastIntentLocked` (trích: `if (intent.getComponent() != null) { ... getReceiverInfo(...) } else { ... mReceiverResolver.queryIntent(...) }`); bug-class tương tự đã device-verified ở blamspotdev/j-code-android#26.

## Fix
- Status intent phải là **implicit**: `Intent(ACTION)` — **không** `setComponent`/`Intent(context, cls)`.
- Receiver động bắt buộc match bằng `IntentFilter(action)`.
- Nhưng trên targetSdk 34+, `PendingIntent.getBroadcast(..., FLAG_MUTABLE)` bọc intent implicit mà **không component, không package** sẽ throw `IllegalArgumentException` ngay lúc tạo (Android 14 behavior changes, "Restrictions to implicit and pending intents"). → Thêm `intent.setPackage(context.packageName)`: intent vẫn implicit (component null → dynamic receiver vẫn nhận), đồng thời thỏa rule mutable-PendingIntent.
- Pin contract bằng test host-JVM (primitives, không chạm android.jar stubs): action non-empty + `hasComponent == false` + package non-empty.
- Lưu ý: claim "targetSdk 34+ rejects implicit intents in PendingIntents" là **sai** — implicit intent vẫn hợp lệ; cái bị reject là *mutable* PendingIntent bọc *unscoped* implicit intent.

## Check grep phòng ngừa
```sh
# Intent explicit nhúng vào PendingIntent.getBroadcast nhưng receiver chỉ đăng ký động:
rg -n "PendingIntent.getBroadcast" --type kotlin -g '!*Test*'
# rồi kiểm tra từng call-site: Intent( phải là Intent(ACTION) + setPackage, KHÔNG Intent(ctx, Cls::class.java)
rg -n "Intent\(.*::class\.java\)" lsmodule/src/main --type kotlin | rg -i "status|pending|broadcast"
# Contract guard: mọi newStatusSender-like helper phải gọi validateStatusIntent
rg -n "getBroadcast" lsmodule/src/main --type kotlin
```
Quy tắc: **receiver động ⇒ intent implicit (action + setPackage, không component)**; **receiver manifest ⇒ intent explicit**.
