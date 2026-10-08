# Bug pattern: Kotlin `val` không được gán trong cả `try` lẫn `catch`

## Triệu chứng
CI đỏ tại `compileDebugKotlin`:
`e: HookErrorStore.kt:146:13 'val' cannot be reassigned.`
Code đã qua 1 writer + 3 round reviewer fresh-eyes mà không ai bắt được.

## Root cause
Idiom Java mang sang Kotlin:
```kotlin
val spxVersion: String
try {
    spxVersion = "..."
} catch (_: Throwable) {
    spxVersion = ""   // ERROR: 'val' cannot be reassigned
}
```
Kotlin definite-assignment: `val` chỉ được gán đúng 1 lần trên mọi path —
gán trong cả `try` và `catch` bị từ chối (kể cả khi logic "chỉ 1 nhánh chạy").

## Fix
Dùng try-as-expression, bundle nhiều field vào data class:
```kotlin
val env: EnvInfo = try {
    EnvInfo(spxVersion = "...", /* ... */)
} catch (_: Throwable) {
    EnvInfo(spxVersion = "", /* ... */)
}
```

## Check phòng (chạy được)
- Không Gradle local trong sandbox → CI là gate duy nhất. Reviewer checklist
  bổ sung: mọi `val x: T` khai báo không initializer phải được gán đúng 1 lần —
  grep `^ *val \w+ *:` không có `=` rồi kiểm tra số chỗ gán.
- Commit: `4bbb416` (spoofx-accurate-logging P1).
