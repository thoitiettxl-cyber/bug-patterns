# Test treo vĩnh viễn vì Future của task bị reject thầm lặng

## Triệu chứng
CI kẹt 40+ phút ở step "Test :lsmodule release unit tests", không fail, không xong.
Run phải cancel tay (GitHub timeout mặc định 6h).

## Root cause
`ThreadPoolExecutor` bounded (queue 128) + rejection handler **nuốt thầm lặng**
(chỉ `incrementAndGet()`, không throw). `AbstractExecutorService.submit()` bọc task
trong FutureTask rồi gọi `execute()` — khi bị reject mà handler không throw,
FutureTask mãi ở trạng thái NEW, `.get()` block **vĩnh viễn**.

Trong `TelemetryDroppedTest.drain()`:
```kotlin
TELEMETRY_EXECUTOR.submit { }.get()   // treo nếu probe bị drop
```
Test overflow cố ý làm đầy queue (128 task + gate latch giữ thread duy nhất);
`drain()` gọi ngay sau `gate.countDown()` — race: worker thread chưa được OS
schedule để rút queue → probe bị reject → Future không bao giờ complete → treo.

## Fix
`drain()` retry với timeout: submit probe, `get(10, TimeUnit.SECONDS)`,
`TimeoutException` → submit lại cho tới khi probe thực sự chạy.

## Check phòng
- Mọi `.get()` trên Future từ executor có rejection-handler-nín-thầm phải có timeout.
- Test nào cố ý overflow queue thì `drain()`/cleanup sau đó phải chịu được reject.
- Reviewer check: rejection handler có throw không? Nếu không → mọi consumer của
  Future từ executor đó đều phải timeout.

## Nguồn
SpoofX `spoofx-accurate-logging` P2, 2026-10-06. Commit fix: `fix(test): ...` sau `9cf4ea2`.
