# `serializer<T>()` trong inline reified fun resolve bằng reflection → crash khi restore

- **Triệu chứng:** app crash ngay khi mở, logcat lặp lại trên nhiều process:
  `Serializer for subclass 'a12' is not found in the polymorphic scope of
  'c12'` trên main thread lúc Compose attach. Crash chỉ xảy ra khi
  `rememberSaveable` có bundle cũ để restore (lần mở đầu tiên sau cài đặt
  vẫn lên UI bình thường) → vòng lặp crash cho tới khi xoá task. CI xanh
  vì CI không bao giờ launch app. (SpoofX, 2026-10-01, miuix-nav 0.9.4-rc01,
  bản release obfuscate bằng R8 full mode + `-repackageclasses ''`.)
- **Root cause:** `rememberNavBackStack` của miuix-nav khai báo
  `inline fun <reified T : NavKey>` và gọi `serializer<List<T>>()` *bên
  trong* hàm inline. Tại đó `T` vẫn là type parameter (bound `NavKey`
  không `@Serializable`) nên compiler KHÔNG resolve serializer lúc compile
  mà emit lookup runtime `KClass.serializer()` (xác minh bằng dex
  decompile: `un1.a(c12.class)` → `or0.t(...)` → `new bi1(...)` chính là
  `PolymorphicSerializer`). Lookup reflective không tìm được
  `Companion`/`INSTANCE` trên sealed interface → rớt vào
  `PolymorphicSerializer` với module rỗng. Encode *tình cờ* qua được
  (fallback dùng serializer của runtime class) nên bundle độc vẫn được ghi;
  decode tra scope rỗng → throw. Bất đối xứng encode/decode này là thứ tạo
  ra crash loop: lần chạy 1 ghi bundle độc, mọi lần sau restore là crash.
  KDoc của lib ("reflection-free ... obtained at the call site") là SAI
  với compiler hiện tại — bug nằm trong lib, không phải do obfuscation
  (bản debug không obfuscate cũng dính vì lookup reflective vốn đã sai).
- **Fix:**
  1. Tự viết saver, capture `serializer<List<SpoofXRoute>>()` ở nơi type đã
     concrete (file-level `private val`, không qua type parameter) → compiler
     trỏ thẳng tới generated `SealedClassSerializer`, R8 giữ lại được.
  2. `@SerialName` tường minh cho mọi subclass của sealed route hierarchy:
     discriminator ổn định qua các bản build obfuscate, bundle cũ vẫn đọc
     được sau khi update app.
  3. `decode` bọc `runCatching` → fallback `[Profiles]`, KHÔNG bao giờ throw
     lúc restore (kể cả bundle độc từ bản build lỗi trước đó).
  4. Test unit: roundtrip mọi route, fallback khi payload hỏng, assert
     element serializer KHÔNG phải `PolymorphicSerializer`, và source-shape
     test cấm `rememberNavBackStack` xuất hiện trở lại trong `src/main`.
- **Phòng (check chạy được):**
  ```bash
  # bất kỳ chỗ nào gọi serializer<T>() với T là reified type parameter:
  # decompile kiểm tra có còn KClass.serializer() reflective không
  grep -rn "rememberNavBackStack" lsmodule/src/main --include=*.kt # phải trắng
  # test pin invariant:
  ./gradlew :lsmodule:testDebugUnitTest --tests "*NavBackStackSaverTest*"
  ```
  Quy tắc: `serializer<T>()` chỉ an toàn khi `T` là concrete type tại đúng
  source location gọi nó. Trong `inline fun <reified T>`, muốn chắc chắn thì
  truyền `KSerializer<T>` tường minh từ call site vào, đừng để lib tự
  `serializer()` bên trong.

## Lesson phụ (2026-10-01, CI fail 2 lần khi push fix)
- miuix-nav khai báo `kotlinx-serialization-json` ở scope **runtime** trong POM →
  code app dùng `Json` trực tiếp sẽ `Unresolved reference` ở compile. Phải khai
  báo `implementation(libs.serialization.json)` trực tiếp, version align với
  miuix (1.11.0).
- kotlinx-serialization **1.11.0 đã xóa public `builtins.ListSerializer`**
  (verify bằng tay trên jar core-jvm 1.11.0: package builtins chỉ còn
  BuiltinSerializersKt, InstantComponentSerializer, LongAsStringSerializer).
  Test assert serializer phải đi qua `descriptor.getElementDescriptor(0)`:
  `serialName == FQCN` (không phải `kotlinx.serialization.Polymorphic`) và
  `kind == PolymorphicKind.SEALED`.

## Root cause ĐẦY ĐỦ (đào sâu 2026-10-01 sau 3 lần CI fail)
Triệu chứng ban đầu ("reflective lookup vì T là type parameter") chỉ là MỘT
NỬA sự thật. Đào sâu khi test `serializer<List<SpoofXRoute>>()` ở call site
concrete VẪN fail mới lòi ra: **module chưa từng apply
`org.jetbrains.kotlin.plugin.serialization`** — `@Serializable` trong
Route.kt chỉ là annotation inert, KHÔNG có `$serializer` nào được generate.
Mọi `serializer<T>()` trong app code đều rớt về reflective lookup.

Hai lớp root cause, phải fix CẢ HAI:
1. Thiếu plugin `kotlin("plugin.serialization")` → không có generated
   serializer nào cả. Fix: khai báo trong version catalog + apply ở module.
2. `rememberNavBackStack` là `inline fun <reified T>` gọi
   `serializer<List<T>>()` khi T còn là type parameter → ngay cả KHI đã có
   plugin, compiler vẫn emit reflective lookup thay vì direct reference.
   Fix: `NavBackStackSaver` tự capture `serializer<List<SpoofXRoute>>()`
   ở chỗ type concrete.

Check phòng ngừa: `grep -rn "plugin.serialization" <module>/build.gradle.kts`
phải có hit khi module dùng `serializer<T>()` / `@Serializable`.
