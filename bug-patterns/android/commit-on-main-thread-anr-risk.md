# commit() đồng bộ (kể cả binder IPC) trên main thread → nguy cơ ANR

## Triệu chứng
Toggle UI gọi `ProfileRepository.setProfileEnabled` /
`CameraConfigRepository.save` — cả local `commit()` lẫn remote binder
`commit()` chạy đồng bộ trên main thread. Binder tắc → ANR.

## Root cause
`SharedPreferences.commit()` là synchronous disk write; remote prefs còn
là binder IPC sang process khác. Đặt cả hai trên main thread từ UI toggle
là vi phạm nguyên tắc không blocking-I/O trên main.

## Fix
- Bọc toàn bộ write trong single-thread executor (daemon, FIFO):
  `toggleIo` / `configIo`. Giữ nguyên semantics (local-commit-checked →
  early return; remote null/fail → dirty flag để reconciler đẩy sau).
- Local write giữ trong `synchronized(repo)` (thay cho `@Synchronized`
  đã bỏ vì body giờ async); remote fetch + binder commit để NGOÀI
  monitor để IPC tắc không block readers.
- Không dùng `Dispatchers.IO`: single thread cho FIFO chặt (pool có thể
  đảo thứ tự toggle on→off nhanh), zero dependency mới.
- UI giữ state local riêng (set trước khi gọi repo) nên không có
  read-after-write đồng bộ nào vỡ; eventual consistency qua dirty-flag.

## Check chạy được
- CI `:lsmodule:test` + `assembleRelease` xanh.
- Máy thật: bật/tắt toggle nhanh liên tục → không ANR, thứ tự on→off
  được giữ, giá trị cuối cùng đúng sau reconciler.
- Phòng: mọi `commit()` (đặc biệt binder IPC) phải ra khỏi main thread;
  grep `\.commit\(\)` định kỳ trong data layer.
