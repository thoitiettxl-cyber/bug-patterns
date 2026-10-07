# Kotlin — gọi overload không tồn tại, CI mới bắt được

Triệu chứng: CI `:lsmodule:compileDebugKotlin` FAILED —
`e: BuildFingerprint.kt:47:19 Argument type mismatch: actual type is
'ByteArray!', but 'String' was expected.`

Root cause: `certSha256Hex()` gọi `sha256Hex(first.toByteArray())`
(ByteArray) nhưng trong file chỉ định nghĩa `sha256Hex(s: String)`.
Kotlin không tự convert ByteArray→String, và lỗi này KHÔNG lòi khi review
tĩnh bằng mắt (audit batch B soi kỹ vẫn sót) vì tên hàm giống nhau —
chỉ compiler mới bắt. Càng nguy hiểm khi sandbox không chạy được Gradle
nên không ai compile thử trước merge.

Fix: thêm overload `sha256Hex(bytes: ByteArray)`, để bản String delegate
qua bản ByteArray:
```kotlin
private fun sha256Hex(s: String): String = sha256Hex(s.toByteArray(Charsets.UTF_8))
private fun sha256Hex(bytes: ByteArray): String =
    MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it) }
```
(SpoofX `dev-codex` commit `c280b41`, 2026-10-03.)

Phòng:
- Mọi nhánh feature merge vào trunk đều phải có CI xanh TRƯỚC (push nhánh
  → chờ run xong → mới merge). Trường hợp này merge thẳng mà không chạy CI
  trên nhánh feature nên lỗi lọt vào `dev-codex`.
- Check grep trước khi đẩy code gọi hàm tự viết: mỗi call-site `sha256Hex(`
  phải có đúng 1 định nghĩa khớp signature —
  `grep -n "fun sha256Hex" <file>` so với `grep -n "sha256Hex(" <file>`.
