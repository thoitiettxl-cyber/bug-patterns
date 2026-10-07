# Vòng poll vô hạn trong `LaunchedEffect` không có giới hạn retry (`HomeScreen`)

- **Triệu chứng:** Nếu module chưa active (chưa root / LSPosed chưa
  enable / scope tắt), coroutine trong `HomeScreen` thức dậy mỗi 1s
  **mãi mãi**, kể cả khi tab Home đã offscreen — pager giữ Home composed
  nên `LaunchedEffect(Unit)` không bao giờ bị dispose. Wakeup vô tận,
  pin CPU/battery, và là leak logic dù không crash. (SpoofX, 2026-10-02.)
- **Root cause:** vòng `while (!xposedActive) { delay(1000); ... }` không
  có điều kiện dừng ngoài chính signal nó đang chờ; mà signal đó có thể
  **không bao giờ tới** (module chưa load). `LaunchedEffect(Unit)` chỉ
  restart khi composable rời/khởi tạo lại composition — pager offscreen
  ≠ dispose. Kết hợp 2 cái = poll vô hạn.
- **Fix (giữ nguyên behavior khi module active bình thường — vòng thoát
  ngay khi bind tới):**
  ```kotlin
  private const val XPOSED_POLL_MAX_ATTEMPTS = 60

  var xposedActive by remember { mutableStateOf(app?.xposedService != null) }
  LaunchedEffect(Unit) {
      var attempts = 0
      while (!xposedActive && attempts < XPOSED_POLL_MAX_ATTEMPTS) {
          delay(1000)
          xposedActive = app?.xposedService != null
          attempts++
      }
  }
  ```
  Hết ~60s mà chưa active thì dừng hẳn; user mở lại app (re-compose)
  hoặc pull-to-refresh sẽ bắt đầu poll mới. Comment ngắn trong code giải
  thích tại sao có giới hạn.
- **Phòng (check chạy được):**
  ```bash
  # tìm mọi vòng poll trong LaunchedEffect/rememberCoroutineScope không có bound:
  rg -n -U "LaunchedEffect\([^)]*\) \{[^}]*while" --glob '*.kt' lsmodule/src/main/java/com/thoittxl/spoofx/ui
  # hoặc đơn giản: mọi `while (` trong ui/ phải có một trong:
  # counter < MAX, SystemClock.elapsedRealtime() deadline, hoặc isActive check
  rg -n "while \(" --glob '*.kt' lsmodule/src/main/java/com/thoittxl/spoofx/ui
  ```
  Luật: **mọi poll loop chờ signal ngoài (service bind, root, network)
  trong Compose phải có bound** — số lần retry tối đa hoặc deadline thời
  gian — vì signal có thể không bao giờ tới và offscreen ≠ dispose.
- **Nguồn:** SpoofX `lsmodule/.../ui/screen/home/HomeScreen.kt`
  (poll `xposedService`), fix batch-2 2026-10-02 trên nhánh `dev-codex`.
