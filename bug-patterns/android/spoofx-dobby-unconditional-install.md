# spoofx-dobby-unconditional-install — hook Dobby cài vô điều kiện, toggle chỉ gate hành vi

## Triệu chứng
- SpoofX v19.8 (chứa B7 `1921538` — sensor spoof native qua Dobby, HMA-APK
  lesson L1): cài 2026-10-05 23:07:04 +07 → app Claude ANR treo (main thread
  `futex_wait`), Play Store native crash loop 8 lần/3 phút. Bỏ scope → hết.
- Boss bisect: `d339b3e` (B6) mở được → `1921538` (B7) gãy.

## Root cause
`ensureSensorHookInstalled()` được gọi **vô điều kiện** từ
`on_library_loaded` (`hook_install.cpp:243`, trong
`namespace spoofx::native::detail`) khi linker báo `libandroid.so` load —
trong MỌI process được scope. Toggle `spoof_sensors` (default OFF) chỉ gate
`g_sensorSpoofEnabled` (hành vi rewrite payload trong replacement), KHÔNG
gate việc cài hook. Trên Android 16 (máy Boss) việc Dobby patch
`ASensorEventQueue_getEvents` trong process không hề dùng sensor đã đủ để
treo/crash.

## Fix
Armed gate 2 lớp (`spoofx-b7-armed-gate`):
1. `std::atomic<bool> g_sensorArmed{false}` — detail scope, external linkage
   (extern decl trong `internal.h`, như `g_sensorSpoofEnabled`).
2. Set `g_sensorArmed = true` (release) cuối `initSensorSpoofBridge` — JNI
   entry này chỉ tới được khi toggle ON qua `SensorSpoofModule.install`.
3. Đầu `ensureSensorHookInstalled()`: `if (!armed) { one-shot log
   "gate refused"; return false; }` (static atomic đã-log, đúng 1 lần/process).
4. Poison flag `g_sensorPoisoned{false}` (anonymous namespace,
   `sensor_spoof.cpp`): `DobbyHook` fail (rc!=0 hoặc trampoline null) →
   poison, `ensureSensorHookInstalled()` return false khi poisoned (cấm retry
   — tránh double-patch prologue rách). `resolveSymbol` fail KHÔNG poison
   (giữ fallback load-muộn).
5. `on_library_loaded`: chỉ gọi `ensureSensorHookInstalled()` khi đã armed
   (boundary enforcement tại trigger site; callee tự re-check).
- Không đổi `my_ASensorEventQueue_getEvents`, không đổi trigger (b) từ JNI
  ngoài arming. Nguyên tắc rút ra: **"default OFF" phải có nghĩa là không
  đụng vào process** — hook cài vô điều kiện + gate hành vi là nửa vời;
  staging contract "eager install" chỉ hợp lý cho hook đã chứng minh an toàn
  khi inert.

## Check (chạy được)
```sh
cd ~/workspace/SpoofX
# 1. Không còn đường gọi install vô điều kiện từ on_library_loaded:
grep -n -B2 -A4 'ensureSensorHookInstalled()' \
  lsmodule/src/main/cpp/spoofx_native/hook_install.cpp
# kỳ vọng: call site nằm trong `if (g_sensorArmed.load(std::memory_order_acquire))`

# 2. armed được set đúng 1 nơi (toggle-ON path) và check ở mọi trigger:
grep -rn 'g_sensorArmed' lsmodule/src/main/cpp/spoofx_native/ \
  | grep -v Binary
# kỳ vọng: extern decl (internal.h), định nghĩa + store true
# (sensor_spoof.cpp, cuối initSensorSpoofBridge), 2 chỗ load-check
# (ensureSensorHookInstalled + on_library_loaded)

# 3. Commit fix tồn tại trong history:
git log --oneline --grep='b7-armed-gate' -3
# kỳ vọng: thấy commit landing của chiến dịch spoofx-b7-armed-gate
```
