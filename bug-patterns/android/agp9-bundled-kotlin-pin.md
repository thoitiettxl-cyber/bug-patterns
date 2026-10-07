# AGP 9 bundle Kotlin 2.2.0 — Miuix 0.9.4 cần compiler ≥ 2.4

- **Triệu chứng:** `:lsmodule:compileDebugKotlin` fail hàng loạt
  `Module was compiled with an incompatible version of Kotlin. The binary
  version of its metadata is 2.4.0, expected version is 2.2.0`
  (+ `Unresolved reference 'run'/'mutableListOf'`... giả do stdlib 2.4.10
  không đọc được). Catalog đã khai `kotlin = "2.4.10"`. (SpoofX,
  2026-10-01, AGP 9.3.2 + Gradle 9.7.1.)
- **Root cause:** AGP 9 bỏ plugin `org.jetbrains.kotlin.android`, thay bằng
  Kotlin support built-in — nhưng compiler đi kèm là **Kotlin 2.2.0 do AGP
  bundle**, không phải version trong catalog. Dependency transitive
  `kotlin-gradle-plugin` từ plugin `org.jetbrains.kotlin.plugin.compose`
  (2.4.10) KHÔNG thắng được compiler AGP bundle (đã apply compose plugin
  mà compiler vẫn là 2.2.0 — verify từ CI log).
- **Fix (E-Muse đã chứng minh, SpoofX áp dụng):** pin trực tiếp vào
  buildscript classpath ở root `build.gradle.kts` (chỉ classpath,
  KHÔNG apply plugin — apply `kotlin.android` bị AGP 9 hard-error):
  ```kotlin
  buildscript {
      dependencies {
          classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.4.10")
      }
  }
  ```
  Version hard-code vì `libs` không truy cập được trong block `buildscript`;
  comment trong file nhắc sync tay với `gradle/libs.versions.toml`.
- **Phòng (check chạy được):**
  ```bash
  # nâng AGP major hoặc thêm lib Kotlin mới: kiểm tra compiler thật
  # (đọc CI log compileDebugKotlin, tìm "incompatible version of Kotlin")
  grep -rn "kotlin-gradle-plugin" build.gradle.kts gradle/libs.versions.toml
  # hai chỗ phải cùng version; nếu lệch -> metadata mismatch
  ```
  Luật: **AGP 9 + lib compile bằng Kotlin mới (Miuix) → luôn pin
  `kotlin-gradle-plugin` trong buildscript, đừng tin catalog version.**
- **Nguồn:** SpoofX CI run `36843687248` (fail) → fix pin 2.4.10,
  2026-10-01. Pattern gốc: E-Muse `build.gradle.kts` (2026-09-30).
