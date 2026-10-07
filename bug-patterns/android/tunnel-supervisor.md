# Tunnel supervisor: generation guard + fail-fast

- **Triệu chứng:** Đổi config (token/hostname) lúc tunnel đang chạy → config
  mới không apply, hoặc supervisor cũ kill nhầm process mới. Thiếu hostname
  mà có token → retry vô hạn, mỗi 60s kill 1 process khỏe mạnh. (E-Muse.)
- **Root cause:**
  - Supervisor là coroutine loop; khi config đổi phải hủy supervisor cũ, nếu
    không 2 loop cùng quản 1 process (BL1).
  - `waitForUrl` không bao giờ match khi thiếu hostname → loop retry giết
    process đang healthy (should-fix 7).
- **Fix:**
  - `generation: AtomicInteger` — mỗi lần đổi config tăng generation, loop cũ
    thấy generation lệch thì tự dừng (BL1).
  - Fail-fast: token có mà hostname trống → báo lỗi ngay, không start.
  - `start()` idempotent: config không đổi thì return, không restart thừa.
- **Phòng:** bất kỳ manager nào có "supervisor loop + restart khi đổi config"
  đều cần generation guard. Review checklist: đổi config lúc đang chạy →
  có restart đúng 1 lần? thiếu field bắt buộc → có fail-fast?
- **Nguồn:** E-Muse `TunnelManager` (BL1, should-fix 7).
