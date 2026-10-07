# Telemetry đọc Throwable sau khi scrub mutate cùng instance (race)

Triệu chứng: fail-open telemetry (P1 `persistFailOpen`) enqueue `(hookKey, t)`
lên `TELEMETRY_EXECUTOR` rồi return ngay; `safeHook` gọi
`scrubModuleFrames(t)` — mutate **cùng instance** (strip frame
`com.thoittxl.spoofx.*`) — ngay sau đó trên interceptor thread. Thread
telemetry đọc `t.stackTrace` **sau** khi đã bị strip → `stackTop` gửi về
manager không còn frame spoofx nào, mất đúng thông tin cần để debug
("chứa frame spoofx" là acceptance của batch P1).

Root cause: producer/consumer chia sẻ mutable `Throwable` qua biên thread mà
không copy dữ liệu cần thiết trước khi hand-off. `scrubModuleFrames` trả về
cùng instance (giữ `===` cho F2 attribution) nên mọi field đọc muộn đều thấy
bản đã strip. L5 (lsposed-safety) cấm lock/IPC trên interceptor thread nhưng
**không cấm đọc field đồng bộ** — capture tại chỗ là hợp lệ.

Fix (SpoofX `dev-codex`, campaign spoofx-accurate-logging P1): trong
`persistFailOpen`, **đồng bộ** trên interceptor thread capture
`CapturedFailure(threadName, stackTop)` — chỉ đọc `Thread.currentThread().name`
+ `t.stackTrace.take(10)` (plain field reads, không lock/IPC) — rồi mới enqueue
`(hookKey, t, captured)`. `HookErrorStore.record()` nhận captured, **không tự
đọc `t.stackTrace` nữa**. Mọi thứ cần IPC (version app, profile...) resolve
trên telemetry thread trong `record()`.

Check phòng chạy được:
```
# Mọi đường đọc t.stackTrace / t.message sau enqueue đều đáng ngờ:
grep -rn "stackTrace" lsmodule/src/main/java/com/thoittxl/spoofx/arch/ \
  | grep -v "persistFailOpen" | grep -v "scrubModuleFrames"
# (kỳ vọng: chỉ còn scrubModuleFrames tự mutate + capture trong persistFailOpen)
```
Quy tắc tổng quát: **dữ liệu telemetry đi qua biên thread phải được snapshot
(copy) ở phía producer trước khi hand-off** — không bao giờ đọc lại mutable
shared state ở phía consumer khi producer còn quyền mutate nó.
