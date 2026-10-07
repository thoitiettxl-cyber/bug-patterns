# Vuốt tắt kill foreground service (swipe-kill)

- **Triệu chứng:** Bật "Chạy nền" + bóng nổi, vuốt app khỏi recents → service,
  bóng nổi, tunnel "mất luôn", không tự về. (E-Muse, Boss báo 2026-09-30.)
- **Root cause:** Trên OnePlus/OxygenOS/ColorOS (và nhiều OEM TQ), vuốt task
  là kill cả process — kể cả foreground service. `START_STICKY` chỉ là "xin"
  restart, OEM thường drop hoặc delay rất lâu. App không override
  `onTaskRemoved()` nên không có gì chủ động hồi sinh service.
- **Fix (E-Muse `62764e2`):**
  ```kotlin
  override fun onTaskRemoved(rootIntent: Intent?) {
      super.onTaskRemoved(rootIntent)
      if (userStopped) return
      runCatching {
          ContextCompat.startForegroundService(this, Intent(this, MuseService::class.java))
      }.onFailure { Log.w(TAG, "onTaskRemoved: self-restart rejected", it) }
  }
  ```
  - `userStopped` set `true` khi nhận `ACTION_STOP`, `false` ở mọi start khác —
    tránh hồi sinh service khi user đã tắt tay (đóng race stopSelf chưa xong).
  - `runCatching` vì Android 12+ có thể reject FGS start từ background trên
    một số ROM; khi đó fallback về START_STICKY.
  - Manifest: `android:stopWithTask="false"` explicit (dù là default).
  - `onCreate()` phải tự khôi phục đủ state (bóng nổi theo prefs, MCP server,
    tunnel) vì restart = process mới.
- **Phòng (check chạy được):**
  ```bash
  # mọi foreground service phải có onTaskRemoved
  grep -rL "onTaskRemoved" --include="*.kt" app/src | xargs grep -l "startForeground" 
  # manifest phải có stopWithTask="false" cho service chạy nền
  grep -A3 '<service' app/src/main/AndroidManifest.xml | grep -c 'stopWithTask="false"'
  ```
- **Lưu ý:** code không thắng được task-killer của OEM hoàn toàn. Trên OnePlus
  vẫn phải hướng dẫn user: khóa app trong đa nhiệm + pin "Không hạn chế".
- **Nguồn:** E-Muse commit `62764e2`, 2026-09-30.
