# Xposed before-hook: set param.result = null cho method trả primitive → crash target

## Triệu chứng
Process app bị hook (ở đây là Facebook) crash với NPE / unboxing error ngay
khi một launch call bị chặn. Logcat hiện lỗi unbox ở phía framework, không
phải do code hook throw (callback vẫn chạy bình thường).

## Root cause
Trong `hookBefore`, gán `param.result` sẽ **skip** method gốc. Nhưng nếu
method gốc trả về **primitive** (`int`, `boolean`, ...) và `param.result`
được gán `null`, framework phải unbox `null` về primitive khi trả kết quả
cho caller → NPE → target process crash.

Vụ thật: `FacebookAdsRemoverModule.hookGameAdActivityLaunchMethod` hook các
method launch có `Intent` param (`LAUNCH_METHOD_NAMES`: `execStartActivity`,
`startActivity`, `startActivityForResult`, `startActivityIfNeeded`) trên
`Instrumentation`, `Activity`, `ContextWrapper`. Code cũ:

```kotlin
param.result = if (method.returnType == Boolean::class.javaPrimitiveType) false else null
```

- `startActivityIfNeeded` trả `boolean` → đã xử lý đúng (`false`).
- `Instrumentation.execStartActivity` trả primitive **`int`** → rơi vào nhánh
  `else null` → framework unbox `null` → **crash Facebook**.
- `startActivity*` / `startActivityForResult` trả `void` → `null` là an toàn.

## Fix
Branch theo `returnType`, KHÔNG bao giờ gán `null` cho primitive:

```kotlin
param.result = when {
    method.returnType == Boolean::class.javaPrimitiveType -> false
    method.returnType == Int::class.javaPrimitiveType -> 0 // ActivityManager.START_SUCCESS: chặn lặng lẽ
    else -> null // void và các kiểu object: null an toàn
}
```

`0` cho `execStartActivity` tương đương `START_SUCCESS`: caller tưởng launch
thành công, không throw, không retry — chặn ad activity một cách lặng lẽ.
Các method còn lại (`void`, `boolean`) giữ đúng behavior cũ.

## Check phòng ngừa
```bash
# Mọi chỗ gán param.result trong before-hook (skip method gốc)
rg -n 'param\.result\s*=' --type kotlin lsmodule/src/main/java/com/thoittxl/spoofx/hooks/ -B2 | rg -n 'hookBefore|param\.result'
# Kiểm tra từng hit: nếu method được hook có thể trả primitive (int/long/boolean/...),
# phải branch theo method.returnType, không gán null mù.
```
Luật: before-hook gán `param.result` → luôn kiểm tra `method.returnType`;
primitive (kể cả `void`? — void gán null OK) phải có giá trị default hợp lệ,
không bao giờ `null`.
