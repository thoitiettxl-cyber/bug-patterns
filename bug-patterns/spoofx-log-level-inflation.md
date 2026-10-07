# spoofx-log-level-inflation — nhánh throwable "tiện tay" Log.e

## Triệu chứng
- `logW("reflection miss …", t)` và `logI(…, t)` trong hook modules hiện ra
  logcat ở level **ERROR** (đỏ), dù caller chỉ định WARN/INFO.
- Hậu quả: logcat bị "ERROR" giả lấn át, triage thật/giả lẫn lộn; vi phạm
  `logging-rules.md` (Log.e chỉ dành cho genuine error: invariant bị phá vỡ).

## Root cause
`lsmodule/src/main/java/com/thoittxl/spoofx/arch/Logging.kt`,
`private fun log(priority: Int, msg: String, tr: Throwable?)`:

```kotlin
if (tr == null) Log.println(priority, DEFAULT_TAG, tagged)
else Log.e(DEFAULT_TAG, tagged, tr)   // ← BUG: bỏ priority, hard-code ERROR
```

Nhánh `tr != null` dùng overload `Log.e(tag, msg, tr)` của SDK thay vì giữ
`priority` — copy-paste "tiện tay" vì `Log.e(tag, msg, tr)` là overload duy
nhất của SDK nhận Throwable trực tiếp. Nhánh `tr == null` và Xposed mirror
(`XposedRef.peek()?.log(priority, …)`) thì đã đúng priority, nên bug chỉ lộ
khi log có gắn throwable.

## Fix
Giữ đúng `priority` của caller, flatten stack trace vào message:

```kotlin
// tr != null: keep the caller's priority instead of inflating to ERROR —
// flatten the stack trace into the message via getStackTraceString.
else Log.println(priority, DEFAULT_TAG, tagged + "\n" + Log.getStackTraceString(tr))
```

`Log.getStackTraceString(tr)` là SDK chuẩn (API 1). Không đổi Xposed mirror
(vốn đã truyền đúng priority). Không ảnh hưởng R8: proguard chỉ strip
`Log.d/v`, `println` với INFO/WARN/ERROR được giữ (logging-rules.md).

## Check chạy được (phòng tái diễn)
1. **Grep invariant**: mọi call site `Log.e(` trong `arch/` phải không có
   `priority` param nào bị bỏ — hoặc đơn giản: `grep -rn "Log\.e("
   lsmodule/src/main/java/com/thoittxl/spoofx/arch/` và đối chiếu từng chỗ
   với level mà caller khai báo.
2. **Unit/JVM test đề xuất**: gọi `logW("m", RuntimeException("t"))` với
   robolectric/shadow `Log.println` và assert priority == `Log.WARN`
   (hiện repo chưa có — ghi nhận để P2+ bổ sung).
3. **Device check**: `adb logcat -s SpoofX` sau khi trigger một `logW(…, t)`
   (vd reflection miss trên target mới) — dòng phải hiện tag WARN, không đỏ.
4. **Quy tắc tổng quát**: khi wrapper log nhận `priority` param, nhánh nào
   cũng phải dùng nó — overload SDK "tiện tay" (`Log.e(tag,msg,tr)`) là
   cái bẫy; review diff thấy `Log.e` trong hàm có `priority` param → hỏi ngay.

Phát hiện: 2026-10-06, chiến dịch `spoofx-accurate-logging` batch P0.
Fix: commit của batch P0 (branch `dev-codex`), CI là proof.
