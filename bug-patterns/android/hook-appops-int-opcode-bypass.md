# Bug pattern: AppOps mask bypass qua int-opcode overload

## Triệu chứng
Module hook `AppOpsManager.checkOp*` / `noteOp*` chỉ xử lý first-arg dạng
`String` (`as? String`), nhưng detector gọi
`checkOpNoThrow(AppOpsManager.OP_MOCK_LOCATION /*int*/, uid, pkg)` — với
int constant — và thấy `MODE_ALLOWED`. Mask bị bypass hoàn toàn, không log,
không crash.

## Root cause
Mọi entry point `checkOp` / `checkOpNoThrow` / `unsafeCheckOp*` /
`noteOp*` đều có **hai overload**: `(String op, …)` và `(int op, …)`.
Int là form phổ biến trong detector (dùng `AppOpsManager.OP_*`
constants). Branch String-only bỏ qua chúng vì cast `as? String` trả về
`null` → hook không làm gì → method thật chạy.

## Fix
Resolve int → public name bằng `@hide`
`AppOpsManager.opToPublicName(int)` qua stub refine
`AppOpsManagerHidden`, rồi so sánh case-insensitive và strip prefix
`"android:"` — giữ nguyên nhánh String cũ. Mẫu đã được chứng minh trong
`AppOpsHideModule.shouldSpoof`:

```kotlin
val name = when (first) {
    is String -> first.lowercase()
    is Int -> {
        val translated = try {
            AppOpsManagerHidden.opToPublicName(first)
        } catch (_: Throwable) {
            // Op code out-of-range throw trên AOSP → coi như không match.
            null
        }
        translated?.lowercase() ?: return false
    }
    else -> return false
}
val stripped = name.removePrefix("android:")
```

## Check grep phòng ngừa
```bash
# Tìm mọi hook AppOps chỉ cast String:
rg -n 'as\? String' lsmodule/src/main/java/com/thoittxl/spoofx/hooks/*AppOps*.kt \
    lsmodule/src/main/java/com/thoittxl/spoofx/hooks/*MockLocation*.kt
# → bất kỳ hook nào trên checkOp*/noteOp* chỉ xử lý String đều phải thêm
# nhánh Int qua opToPublicName.
```

## Ví dụ trong repo
- `HideMockLocationModule.kt::isMockLocationOp` — fix 2026-10-02 (batch 3, bug 2)
- `AppOpsHideModule.kt::shouldSpoof` — pattern chuẩn
