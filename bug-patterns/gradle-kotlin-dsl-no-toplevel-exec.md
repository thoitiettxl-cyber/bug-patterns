# Gradle Kotlin DSL: không exec{} ở top-level, không dùng FQN java.io

**Ngày:** 2026-10-07 — SpoofX `build.gradle.kts`, CI đỏ `ScriptCompilationException` (5 errors).

## Triệu chứng
Thêm block top-level trong `lsmodule/build.gradle.kts`:
```kotlin
val out = java.io.ByteArrayOutputStream()
exec {
    commandLine("git", "rev-parse", "--short", "HEAD")
    ...
}
```
CI fail ngay ở script compilation:
- `Unresolved reference 'io'` (cho `java.io.ByteArrayOutputStream`)
- `Unresolved reference 'exec'` (rồi kéo theo `commandLine`, `workingDir`, `standardOutput`)

## Root cause
Trong Kotlin DSL script, `exec {}` top-level không resolve (dù là method của Project), và FQN `java.io.X` inline có thể bị shadow/không resolve dù `import java.io.File` ở đầu file vẫn compile bình thường.

## Fix
Đọc `.git/HEAD` trực tiếp bằng `java.io.File` (đã import sẵn ở đầu file, đã chứng minh compile được) — không subprocess, không scope issue:
```kotlin
val gitSha: String = try {
    val head = File(rootDir, ".git/HEAD").readText().trim()
    val full = if (head.startsWith("ref:")) {
        File(rootDir, ".git/" + head.removePrefix("ref:").trim()).readText().trim()
    } else head   // detached HEAD: CI checkout SHA trực tiếp
    full.take(7).ifEmpty { "unknown" }
} catch (_: Exception) { "unknown" }
```

## Check phòng
- Cần git SHA trong build script → đọc `.git/HEAD` bằng File, không exec.
- Mọi thứ dùng trong `.gradle.kts` phải là symbol đã có import/chứng minh compile được trong chính file đó — không assume "cái này Groovy/Kotlin thường chạy được".
- Đổi build script → coi CI là proof bắt buộc (không có compile local trong sandbox).
