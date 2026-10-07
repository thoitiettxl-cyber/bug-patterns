# SpoofX: telemetry trên interceptor thread vi phạm lsposed-safety L5

## Triệu chứng
Audit compliance (campaign `spoofx-compliance-fix`, P1-4): `persistFailOpen`
(`arch/HookUtils.kt`, `@PublishedApi internal inline`) chạy trên interceptor
thread (gọi từ `safeHook` catch → `BeforeAfterHooker.intercept` /
`ReplacementHooker.intercept`). Nó gọi đồng bộ:
- `HookErrorStore.record()` — `synchronized(lock)` (lock acquisition).
- `HookErrorReporter.report()` — `PendingIntent.getBroadcast` + `sendBroadcast`
  (binder IPC tới AMS).

Cả hai vi phạm rule `lsposed-safety.md` L5: "No blocking I/O in an
interceptor. No file reads, disk writes, network, `Thread.sleep`, **lock
acquisition**."

Nguy cơ thực tế: interceptor thread của libxposed chạy bên trong app target;
`synchronized` contention hoặc binder IPC chậm trên đó có thể gây jank/ANR
hoặc reentrancy, trong khi fail-open path phải là "never break the target".

## Root cause
Fail-open telemetry được viết như code thường (record + forward đồng bộ ngay
trong catch), quên rằng nó chạy trên interceptor thread — nơi chỉ được làm
việc non-blocking, không lock, không IPC. Logcat (`Log.w`) thì được phép
(không nằm trong danh sách cấm của L5).

## Fix
Offload toàn bộ `record` + `report` sang single-thread daemon executor riêng
(`TELEMETRY_EXECUTOR` trong `HookUtils.kt`, `@PublishedApi internal` vì được
gọi từ inline function). Interceptor thread chỉ `execute { ... }` rồi return
ngay; `Log.w` giữ trên interceptor thread. Executor:
- single thread → entries giữ thứ tự (khớp id monotonic của `HookErrorStore`),
  target pathological không spawn thread vô hạn;
- daemon thread → không giữ target process sống;
- không bao giờ shutdown → sống suốt vòng đời process (by design, per-process).

Best-effort giữ nguyên: try/catch trong body executor + try/catch quanh
`execute` — telemetry không bao giờ throw vào fail-open path.

## Check phòng
- Grep interceptor path (`intercept`, `safeHook` catch, adapter callback) tìm:
  `synchronized`, `sendBroadcast`, `getBroadcast`, `ContentResolver`,
  `SharedPreferences.edit/commit`, `File(` write, `Thread.sleep`,
  `PendingIntent.get*`.
- Rule: bất kỳ thứ gì lock/IPC/disk trong interceptor → enqueue sang executor
  hoặc dời ra install-time (`onPackageLoaded`).
- `HookModuleRegistry.install` catch vẫn gọi `HookErrorStore.record` đồng bộ
  (install-time, không phải interceptor thread — chấp nhận được; verify
  2026-10-06 trong B3).
