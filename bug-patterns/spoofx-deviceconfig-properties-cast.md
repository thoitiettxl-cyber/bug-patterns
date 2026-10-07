# DeviceConfig$Properties ≠ java.util.Properties: cast mù drop toàn bộ giá trị framework

Triệu chứng: hook `DeviceConfig.getProperties(String, String...)` sau merge
trả về object rỗng (chỉ chứa overrides) — mọi flag framework biến mất, app
đọc được config trống thay vì config thật + overrides.

Case thật (2026-10-05, SpoofX campaign `spoofx-romfix`, bug F1/P0):
`FeatureFlagSpoofModule.hookGetProperties` làm
`val copy = Properties()` + `(param.result as? Properties)?.let { copy.putAll(it) }`.
Trên ROM OP15, `getProperties` trả về `android.provider.DeviceConfig$Properties`
— class public nhưng superclass là `java.lang.Object`, KHÔNG kế thừa
`java.util.Properties`. Safe-cast `as? Properties` luôn fail → `copy` rỗng →
`param.result` = Properties rỗng → drop toàn bộ giá trị framework. Không crash,
không log — fail thầm lặng nên lọt qua review.

Root cause: đoán kiểu trả về từ tên class (`*Properties` → `java.util.Properties`)
thay vì verify trên dex thật. Tên giống nhau ≠ cùng hierarchy.

Fix: đọc giá trị framework qua accessors đã verify trên ROM dex
(`getKeyset()`, `getString(String, String)`), merge overrides (chỉ keys caller
đã request — anti-leak), dựng instance mới ĐÚNG KIỂU qua constructor public
`(String, Map)` đã verify, gán `param.result`. Tuyệt đối không mutate object
của framework (invariant "clone mutable returns"). Mọi reflective lookup fail
→ fail-open giữ nguyên result + log warning (chỉ namespace/key names, no PII).

Evidence verify (OP15 ROM dex,
`apex/com.google.android.configinfrastructure_compressed/framework-configinfrastructure/classes.dex`,
tool `rom_query.py` + access-flags dump):
- `Landroid/provider/DeviceConfig$Properties;`: class acc `0x00000001` (public),
  super `Ljava/lang/Object;`
- public `<init>(Ljava/lang/String;, Ljava/util/Map;)V` (method acc `0x10001`)
- public `getKeyset()Ljava/util/Set;`, `getString(Ljava/lang/String;,Ljava/lang/String;)Ljava/lang/String;`,
  `getNamespace()`, `getInt/getLong/getFloat/getBoolean`, `getPropertyValues()` (acc `0x0001`)
- `DeviceConfig.getProperties(Ljava/lang/String;,[Ljava/lang/String;)Landroid/provider/DeviceConfig$Properties;`
  cùng jar

Phòng:
- Mọi cast `as? <FrameworkType>` trên `param.result` của method `@hide` → verify
  hierarchy thật bằng `rom_query.py --class '<descriptor>'` (xem `super=`) trước
  khi code; không suy từ tên class.
- Unit test merge với fake class đúng shape đã verify: assert (1) framework values
  còn đủ sau merge, (2) instance trả về khác instance framework (không mutate),
  (3) fail-open (trả null) khi shape sai.
- Grep định kỳ `as? Properties` trong `hooks/` — mọi match phải có citation dex.
