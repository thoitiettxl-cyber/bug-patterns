# Kho bug-patterns — bẫy đã biết, đừng mắc lại

Mỗi file = 1 bug pattern từng gây bug thật. Session mới làm việc với domain
tương ứng thì **đọc lesson trước khi code**. Khác với memory (lưu facts),
đây là kho *bẫy*: triệu chứng → root cause → fix → cách phòng bằng check
chạy được.

Quy ước: lesson nào cũng phải có mục **Phòng** — 1 câu lệnh hoặc 1 checklist
item có thể chạy/kiểm tra bằng máy. Lesson không có cách phòng thì chỉ là
chuyện kể.

> **Quy tắc theo nhóm:** xem [`RULES.md`](RULES.md) khi cần nhìn nhanh toàn bộ bẫy.

## Android — service & lifecycle

- `android/swipe-kill-foreground-service.md` — OnePlus/ColorOS vuốt tắt kill cả
  process, START_STICKY restart bị drop. Fix bằng `onTaskRemoved()` tự restart.
- `android/prefs-wipe-cold-start.md` — state khởi tạo rỗng persist đè prefs
  ngay lần chạy đầu → wipe dữ liệu đã lưu.
- `android/overlay-window.md` — `TYPE_ACCESSIBILITY_OVERLAY` chỉ add được từ
  accessibility service context; cấm nuốt exception ở `addView`.
- `android/orphan-child-process.md` — process con (cloudflared...) sống sót
  sau khi service chết → phải dọn `killStaleTunnel`.
- `android/tunnel-supervisor.md` — generation guard khi đổi config lúc đang
  chạy; fail-fast khi thiếu hostname.

## Android — platform gotchas

- `android/native-tls-ca.md` — binary Go/native không đọc system CA store →
  bundle Mozilla CA + `SSL_CERT_FILE`.
- `android/mediaprojection-fgs-type.md` — Android 14+: MediaProjection chỉ tạo
  được trong FGS type `mediaProjection`.
- `android/quick-tunnel.md` — Quick Tunnel QUIC/HTTP2 fail trên một số máy/
  mạng → named tunnel là đường chính.

## Build — compile & API

- `build/verify-api-before-use.md` — luật Context7: mọi claim về compile/API
  phải tra docs mới nhất, cấm đoán. (ProcessHandle, Miuix API, AGP 9.x...)

## Process — quy trình

- `process/secrets.md` — không bao giờ "tái tạo" secret từ trí nhớ; copy
  nguyên văn từ file; config chỉ giữ placeholder.
- `process/verify-artifact.md` — verify artifact bằng máy (revision, chữ ký),
  đừng kết luận bằng mắt. GitHub `archive:false` → API zip trả raw file.
- `process/definition-of-done.md` — checklist giao artifact: cold start,
  reboot, vuốt tắt, đúng máy Boss, không secret.

## Thêm pattern mới

1 bug = 1 file (hoặc 1 mục) ngay trong commit fix. Đặt tên file dạng
`domain/ten-pattern.md`, theo đúng format 5 mục trong các file hiện có.
