# Kotlin — trigger chết: feature "xong" nhưng không có caller (ảo giác hoàn thiện)

Triệu chứng: feature T5 (surface hook errors ra Settings UI) merge xong, CI
xanh, review pass — nhưng trên máy thật badge đỏ KHÔNG BAO GIỜ hiện dù hook
lỗi thật. Mọi test đều "không tái hiện được".

Root cause: T5 nối trigger vào `IHook.hook()` (catch → `HookErrorStore.record`),
nhưng **không có class nào extends `IHook`** (0 subclass, 0 instantiation toàn
repo). Đường chạy thật (`HookModuleRegistry.install()`) catch exception nhưng
chỉ `Log.w`, không gọi `record()`. Spec nhắm đúng "ghi lỗi khi hook lỗi" nhưng
nhắm sai layer — review chỉ soi code MỚI, không grep caller của trigger.

Fix: nối `HookErrorStore.record(e.key, t)` + `HookErrorReporter.report(entry)`
vào nhánh `else` (exception thật) của `HookModuleRegistry.install()` catch —
không record `FingerprintMissException` (skip có chủ ý của T4).
(SpoofX `dev-codex`, audit 2026-10-04, findings A1/A2/P0-1/P0-2.)

Phòng:
- Với mọi feature "khi X xảy ra thì Y": grep TẤT CẢ caller của trigger trước
  khi claim xong — `grep -rn "<trigger>" --include="*.kt" | grep -v <file-def>`.
  Trigger 0 caller = feature chết, dù code đẹp và CI xanh.
- Đặc biệt với catch-block: liệt kê ai có thể throw vào đó (subclass? caller?).
- KDoc mô tả behavior phải khớp wiring thật, không khớp ý định.
