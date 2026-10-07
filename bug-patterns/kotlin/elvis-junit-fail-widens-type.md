# Bug: elvis + JUnit `fail()` widens inferred type to `Any?`

## Triệu chứng
CI `:lsmodule:compileDebugUnitTestKotlin` fail với hàng loạt
`Unresolved reference 'language' / 'country' / 'toLanguageTag' / 'id'`
trên các val được suy kiểu từ `someNullable() ?: fail("...")`,
trong khi các static call (`Locale.getDefault()`) vẫn compile bình thường.

## Root cause
`org.junit.Assert.fail(String)` trả về Java `void` → Kotlin `Unit`,
KHÔNG phải `Nothing`. Nên biểu thức:

```kotlin
val vi = parseLocaleTag("vi-VN") ?: fail("vi-VN must parse")
```

suy kiểu thành `Locale? ?: Unit` → common supertype **`Any?`**.
Mọi member access instance (`vi.language`, `tz.id`) đều unresolved.

Ngược lại `kotlin.io.error("...")` trả về `Nothing` nên elvis giữ nguyên
kiểu `Locale` (non-null) như mong đợi.

## Fix
Thay mọi `?: fail("...")` trong test bằng `?: error("...")`;
xóa `import org.junit.Assert.fail` (tránh `no-unused-imports`).

## Check phòng ngừa
```bash
rg --type kotlin -n '\?: fail\(' lsmodule/src/test/
```
phải trả về rỗng. Nếu muốn assert non-null theo style JUnit, dùng
`assertNotNull(x)` rồi `x!!` cục bộ, hoặc `error()` như trên.

## Ghi nhận
- Phát hiện: CI run 37065148629 (campaign per-app-locale-timezone, L-B2).
- Fix commit: `5336582` trên `dev-codex`.
- Bài học: đừng nhầm `fail()` (JUnit, void) với `error()`/`TODO()` (Kotlin, Nothing)
  khi dùng trong elvis để smart-cast non-null.
