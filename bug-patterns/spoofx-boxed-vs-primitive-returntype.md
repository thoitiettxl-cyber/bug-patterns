# FALSE POSITIVE lesson: `Int::class.java` trong Kotlin LÀ primitive `int.class`

> File này ban đầu ghi "bug pattern F2" — đã được viết lại ngày 2026-10-05 sau
> khi CI chứng minh F2 là **false positive**: không có bug nào cả. Giữ lại như
> bài học chống "fix" sai.

## Chuyện gì đã xảy ra
Chiến dịch ROM-verify báo F2: `SystemPropertiesSpoofModule.NUMERIC_RETURN_TYPES`
dùng `Int::class.java` (tưởng là boxed `java.lang.Integer`) để so với
`Method.getReturnType()` (primitive `int.class`) → filter skip hết overload số.

Batch B2 "fix" bằng `Int::class.javaPrimitiveType!!` + test mới
`SystemPropertiesReturnTypeFilterTest` (6 test). Reviewer 2 pass `correct`.
CI **đỏ**: 3/6 test fail, trong đó
`assertNotEquals(Int::class.java, returnTypeOf("getInt"))` FAIL — tức hai vế
**bằng nhau**. Vì `returnTypeOf("getInt")` chắc chắn là `int.class` (JVM spec),
suy ra **`Int::class.java` == `int.class`** trong Kotlin.

## Root cause của false positive
Trong Kotlin, `Int::class.java` map tới **JVM primitive `int.class`**, KHÔNG
phải `java.lang.Integer` (muốn boxed phải dùng `Int::class.javaObjectType`).
Đây là gotcha kinh điển của Kotlin/JVM reflection. Cả worker ROM-verify,
writer B2, 2 reviewer, và coordinator đều mang tư duy Java
(`Integer.class` vs `Integer.TYPE`) áp vào code Kotlin — không ai verify
premise "Int::class.java là boxed" bằng một test chạy thật trước khi fix.

Hệ quả: code gốc đã đúng từ đầu; "fix" B2 là semantic no-op; test mới encode
premise sai nên đỏ. B2 bị **revert toàn bộ** (commit revert + KDoc cảnh báo
tại chỗ trong `SystemPropertiesSpoofModule.kt`).

## Check chạy được (bài học thật)
- Chính CI failure là proof: `assertNotEquals(Int::class.java, int.class)`
  fail ⟹ `Int::class.java` là primitive. Khi nghi ngờ semantics của
  `KClass.java` / `javaPrimitiveType` / `javaObjectType`, viết một unit test
  3 dòng assert rồi chạy — đừng tin trí nhớ, đừng tin "kinh điển".
- Mapping đúng (Kotlin/JVM): `Int::class.java` = `int.class`;
  `Int::class.javaPrimitiveType` = `int.class` (giống hệt — "fix" F2 là no-op);
  `Int::class.javaObjectType` = `java.lang.Integer`.

## Phòng ngừa
- **Verify premise trước khi fix:** mọi claim "X là boxed/primitive" phải có
  một assertion chạy thật (JVM proof hoặc unit test) TRƯỚC khi viết fix —
  đặc biệt khi claim liên quan Kotlin↔Java reflection mapping.
- Reviewer checklist bổ sung: khi diff đụng `::class.java` / `javaPrimitiveType`
  / `javaObjectType`, reviewer phải tự verify mapping bằng test hoặc citation
  stdlib docs, không tin KDoc/comment của writer.
- False positive cũng là 1 file bug-pattern: ghi lại để lần sau không "fix" lại.

## Ba quy tắc — Boss chưng cất từ vụ F2 (2026-10-05)

Đừng sửa interop Kotlin/Java theo cảm giác "boxed cho an toàn". Kiểm tra
identity của `Class` trước, rồi mới đụng code.

**1. Token kiểu và class của giá trị là hai thứ khác nhau.**
`Int::class.java` là token của kiểu, và nó là primitive `int.class`.
`42.javaClass` là class của một giá trị đã bị box, nên ra `Integer`.
`Int?` và `Int` trong generic cũng bị box. Thấy `Integer` lúc chạy không có
nghĩa `.java` đang trả wrapper.

**2. Ba API không hoán đổi cho nhau.** Với `Int::class`:
- `.java` → `int.class`
- `.javaPrimitiveType` → `int.class` (cùng object, đổi sang đây là semantic no-op)
- `.javaObjectType` → `java.lang.Integer.class`

Chỉ dùng `javaObjectType` khi API Java thật sự cần wrapper: annotation,
generic type token, serializer không nhận primitive. Method/field khai báo
`int` thì phải giữ `int.class`.

**3. Test phải khóa sự thật, không khóa nghi ngờ.**
`assertNotEquals(Int::class.java, int.class)` đóng đinh một premise sai. Nó đổ
thì đó là proof finding sai, không phải proof code gốc hỏng. Trước khi "fix",
in hoặc assert đúng chiều: `Int::class.java == Int::class.javaPrimitiveType`
và `!= Int::class.javaObjectType`. Nếu bằng nhau thì đừng sửa production.

Dấu hiệu false positive: commit đổi chữ mà hành vi không đổi, rồi CI đỏ đúng
cái assertion mới. Lúc đó **revert, đừng vá tiếp test cho khớp giả định**.
