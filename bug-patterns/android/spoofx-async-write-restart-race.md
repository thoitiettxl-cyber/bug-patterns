# spoofx-async-write-restart-race — restart target đua với commit async của repo

## Triệu chứng
- `ProfileRepository.setProfileEnabled` / `setSentinelResetEnabled` chuyển
  sang `toggleIo.execute{}` (U-P2-2, tránh ANR) nhưng `AppConfigScreen`
  vẫn gọi `ReloadReceiver.requestRestart(...)` ngay sau call — restart có
  thể chạy trước khi local/remote commit xong → target relaunch đọc snapshot
  cũ, toggle "không ăn" cho tới lần mở sau.
- Cùng race trong `CameraConfigScreen.publishChange`: KDoc claim "(local +
  remote commit is synchronous inside the setters)" trong khi
  `CameraConfigRepository.save` bọc trong `configIo.execute{}` (async) —
  comment sai + race thật. Một fragment comment dở `// P1-B2 delete: ...`
  còn sót ngay trên KDoc đó.

## Root cause
U-P2-2 background hoá write nhưng không đưa ra barrier hoàn thành: mọi call
site cũ giả định "gọi xong = đã commit". `requestRestart` chỉ gửi broadcast —
nó không đợi gì cả, nên thứ tự thực thi = thứ tự race giữa main thread và
IO thread.

## Fix (chiến dịch spoofx-compliance-fix, B2)
1. `ProfileRepository.setProfileEnabled` / `setSentinelResetEnabled` nhận
   thêm `onDone: () -> Unit = {}`; bọc body `toggleIo.execute` trong
   `try/finally { onDone() }` → callback chạy trên MỌI nhánh (local commit
   fail, remote null, remote fail, exception). Signature cũ tương thích
   (default param).
2. `AppConfigScreen`: `requestRestart` chuyển vào trong `onDone`.
3. `CameraConfigRepository`: thêm `afterPendingWrites(onDone)` — enqueue
   barrier task lên `configIo` (single-thread FIFO → chạy sau mọi write đã
   enqueue). `CameraConfigScreen.publishChange` gọi `update()` rồi enqueue
   barrier và restart trong đó — đúng cho cả lambda 1 setter lẫn
   `clearMedia` (4 setter + `publishChange()` trần). Không cần đổi signature
   7 public setter.
4. Xoá fragment `// P1-B2 delete:`; sửa KDoc `publishChange` cho đúng bản
   chất async + cơ chế barrier.

## Check (chạy được)
```sh
cd ~/workspace/SpoofX
# 1. Mọi đường restart sau write async đều nằm trong callback/barrier:
grep -rn -A3 'requestRestart' \
  lsmodule/src/main/java/com/thoittxl/spoofx/ui/screen/scope/AppConfigScreen.kt \
  lsmodule/src/main/java/com/thoittxl/spoofx/ui/screen/camera/CameraConfigScreen.kt
# kỳ vọng: requestRestart chỉ xuất hiện trong onDone { } / afterPendingWrites { }

# 2. onDone chạy trên mọi nhánh (try/finally bao toàn bộ body execute):
grep -n -A3 'toggleIo.execute' \
  lsmodule/src/main/java/com/thoittxl/spoofx/data/ProfileRepository.kt | head -12
# kỳ vọng: dòng ngay sau execute là `try {`, cuối body là `} finally { onDone() }`

# 3. Không còn claim "synchronous" sai:
grep -rn 'synchronous inside the setters\|P1-B2 delete' lsmodule/src/main --include=*.kt
# kỳ vọng: rỗng
```
