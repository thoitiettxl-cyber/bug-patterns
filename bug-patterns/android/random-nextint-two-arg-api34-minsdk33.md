# Random.nextInt(origin, bound) NoSuchMethodError trên API 33 (minSdk 33)

## Triệu chứng
Crash `NoSuchMethodError: No virtual method nextInt(II)I` ngay khi gọi
`SecureRandom().nextInt(3, 10)` (hoặc `kotlin.random.Random.nextInt(from, until)`)
trên máy Android API ≤ 33. App target API 36, minSdk 33 — crash chỉ xảy ra
trên máy cũ, khó phát hiện nếu dev/test toàn trên API 34+.

## Root cause
`rng` là `java.security.SecureRandom` (kế thừa `java.util.Random`). Dạng 2 đối
số `nextInt(origin, bound)` là API của **JDK 17**, được backport lên Android
chỉ từ **API 34**. Tương tự, `kotlin.random.Random.nextInt(from, until)` của
Kotlin stdlib cũng delegate xuống đúng method đó của `java.util.Random`.
Vì module **không bật core library desugaring** (không có
`isCoreLibraryDesugaringEnabled` trong `compileOptions` và không có
`coreLibraryDesugaring(...)` trong `dependencies` của `lsmodule/build.gradle.kts`),
ART trên API 33 không có method này → `NoSuchMethodError` ở runtime.
Code vẫn compile bình thường vì SDK compile chứa signature đó.

Vụ thật: `DeviceIdRandom.line1()` gọi `rng.nextInt(3, 10)` khi user bấm nút
"Random" — crash app manager trên OnePlus API 33.

## Fix
Dùng dạng 1 đối số `nextInt(bound)` (tồn tại từ Java 1.2, an toàn mọi API) rồi
dịch khoảng bằng tay, giữ nguyên semantics:

```kotlin
// [3, 10) — thay cho rng.nextInt(3, 10)
append(3 + rng.nextInt(7))
```

Nếu thật sự cần 2-arg form, hoặc bật core library desugaring, hoặc yêu cầu
minSdk 34.

## Check phòng ngừa
```bash
# Dạng Java: SecureRandom/nextInt 2 đối số
rg -n '\.nextInt\([^()]*,' --type kotlin lsmodule/src/main/java/
# Dạng Kotlin stdlib: kotlin.random.Random.nextInt(from, until)
rg -n 'Random\.nextInt\([^()]*,' --type kotlin lsmodule/src/main/java/
```
Lệnh trên vẫn match các call hợp lệ kiểu `nextInt(SERIAL_ALPHABET.length)`
(không có dấu phẩy) → không false positive. Mọi hit có dấu phẩy đều phải
review: hoặc rewrite thành `base + nextInt(span)`, hoặc xác nhận desugaring
đã bật trong `lsmodule/build.gradle.kts`.
