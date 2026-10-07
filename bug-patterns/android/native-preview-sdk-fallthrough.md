# Native property fallthrough: key kết thúc `_sdk` không match entry `.sdk`

## Triệu chứng
Java `SystemPropertiesSpoofModule` publish `ro.build.version.preview_sdk =
"0"` (khi CODENAME=REL) nhưng NDK callers (`__system_property_get`)
vẫn nhận giá trị thật của host — cross-layer divergence, đúng kiểu
detection vector mà module này được viết để đóng.

## Root cause
Cascade `getSpoofedValue` trong `state.cpp` thiếu entry `.preview_sdk`.
Key `ro.build.version.preview_sdk` kết thúc bằng `_sdk` (ký tự trước là
`_`, không phải `.`) nên KHÔNG match `ends_with(".sdk")` → fall through
`return nullptr` → `property_hooks.cpp` giữ nguyên value thật từ bionic.
Bionic lookup là full-key exact match trên prop trie (không có suffix
semantics), nên thiếu entry ở native là thiếu thật, không có fallback nào
cứu được.

## Fix
Thêm entry ngay sau `.sdk` trong cascade:
```cpp
if (prop.ends_with(".preview_sdk")) {
    if (strcmp(p->CODENAME, "REL") == 0) return "0";
    return nullptr;
}
```
Invariant-safe: `.preview_sdk` không bị entry `.sdk` nuốt ở bất kỳ thứ tự
nào (và ngược lại). Không cần field mới trong `DeviceProfile` (Java logic
là hằng số khi REL; native đã có `p->CODENAME`).

## Check chạy được
- CI `assembleRelease` xanh.
- Máy thật: trong target process, `__system_property_get(
  "ro.build.version.preview_sdk")` trả `"0"` khi profile CODENAME=REL;
  Java `SystemProperties.getInt` cùng giá trị → parity.
- Phòng: khi Java publish key mới trong `buildMap`, đối chiếu ngay với
  cascade `getSpoofedValue` — mỗi key Java phải có entry native tương ứng
  (trừ khi cả 2 tầng cùng không publish = consistent).
