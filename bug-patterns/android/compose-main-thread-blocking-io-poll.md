# Blocking I/O (`/proc` scan) chạy trên Main qua poll loop trong Compose (`AppConfigScreen`)

- **Triệu chứng:** `restartApp()` (overflow menu "Restart" trong
  `AppConfigScreen`) làm UI jank/giật ~5s sau khi bấm: poll loop
  `while (waited < 5000 && isAppRunning())` với `delay(100)` chạy trên
  `rememberCoroutineScope()` (= Main dispatcher), mà `isAppRunning()`
  liệt kê `File("/proc").listFiles()` + đọc `cmdline` từng PID —
  blocking file I/O trên UI thread. (SpoofX, 2026-10-02.)
- **Root cause:** `isAppRunning()` là `fun` thường (non-suspend), nên
  `withContext(Dispatchers.IO)` không dùng được; `rememberCoroutineScope`
  bind Main dispatcher. Mỗi vòng poll đọc hàng chục file `/proc/<pid>/cmdline`
  ngay trên Main → mỗi lần bấm Restart là 1 đợt ANR-suýt.
  Cái bẫy: `delay(100)` trong loop trông "async" nên dễ tưởng code đã
  không block — nhưng `delay` chỉ nhường giữa 2 lần đọc blocking, không
  dời chính phép đọc ra khỏi Main.
- **Fix (giữ nguyên semantics detect + timeout 5s):**
  ```kotlin
  // /proc scan is blocking file I/O — it must NOT run on the UI thread.
  suspend fun isAppRunning(): Boolean = withContext(Dispatchers.IO) {
      runCatching {
          java.io.File("/proc").listFiles()
              ?.any { dir ->
                  dir.isDirectory && dir.name.all { c -> c.isDigit() } &&
                      java.io.File(dir, "cmdline").inputStream().use {
                          it.readBytes().toString(Charsets.UTF_8).substringBefore('\u0000')
                      } == packageName
              } == true
      }.getOrDefault(false)
  }
  ```
  Call site giữ nguyên (`while (waited < 5000 && isAppRunning())`) vì
  `restartApp()` đã chạy trong `scope.launch` (coroutine) → gọi suspend
  trực tiếp được. Logic detect + cap 5s không đổi.
- **Phòng (check chạy được):**
  ```bash
  # bất kỳ fun non-suspend nào đọc File/InputStream/Runtime.exec
  # mà được gọi từ rememberCoroutineScope()/LaunchedEffect scope Main:
  rg -n "fun \w+\(\)(: Boolean)? = runCatching" --glob '*.kt' lsmodule/src/main/java | while read -r l; do :; done
  # kiểm tra thủ công nhanh: liệt kê các hàm đọc file rồi grep call site
  rg -n "File\(|inputStream\(\)|readBytes\(\)|Runtime.getRuntime\(\)\.exec" --glob '*.kt' lsmodule/src/main/java/com/thoittxl/spoofx/ui | rg -v "withContext\(Dispatchers.IO\)"
  ```
  Luật: **blocking I/O trong composable helper → `suspend fun` +
  `withContext(Dispatchers.IO)` ngay từ đầu**; `delay()` trong poll loop
  không thay thế việc dời I/O ra khỏi Main. (`runSuCommand` trong cùng
  file đã là mẫu đúng để copy.)
- **Nguồn:** SpoofX
  `lsmodule/.../ui/screen/scope/AppConfigScreen.kt` (`isAppRunning`,
  `restartApp`), fix batch-2 2026-10-02 trên nhánh `dev-codex`.
