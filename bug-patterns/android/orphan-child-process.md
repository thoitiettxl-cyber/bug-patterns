# Process con mồ côi sau khi service chết

- **Triệu chứng:** Service restart nhưng tunnel/port bị chiếm, hoặc có nhiều
  cloudflared chạy chồng nhau. (E-Muse, BL2.)
- **Root cause:** `ProcessBuilder`/`Runtime.exec` fork process con. Khi app
  process bị kill (vuốt tắt, crash, force-stop), AMS chỉ kill process của app —
  **process con native không bị kill theo**, thành mồ côi, giữ port/tunnel.
- **Fix:** mỗi lần service start, dọn process mồ côi của lần chết trước
  (`killStaleTunnel()` trong E-Muse `TunnelManager`); `onDestroy` kill process
  con mình đã spawn.
- **Phòng (check chạy được):**
  ```bash
  grep -rn "ProcessBuilder\|Runtime.getRuntime().exec" --include="*.kt" app/src
  # mỗi chỗ spawn phải có chỗ kill tương ứng (onDestroy + cleanup lúc start)
  ```
  Luật: **spawn ở đâu, kill ở đó — và dọn mồ côi lúc start vì không ai đảm bảo
  onDestroy được gọi.**
- **Nguồn:** E-Muse `TunnelManager.killStaleTunnel` (BL2).
