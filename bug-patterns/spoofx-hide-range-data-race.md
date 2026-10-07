# spoofx-hide-range-data-race — `g_hideRanges`/`g_hideRangeCount` plain global, writer/reader khác thread

## Triệu chứng
- Phát hiện qua audit (chiến dịch `spoofx-compliance-fix`, P1-6, 2026-10-06):
  `maps_stealth.cpp:30-31` dùng plain globals `AddrRange
  g_hideRanges[32]` + `size_t g_hideRangeCount`. Writer `addHideRange`
  (`:117-124`) chạy trên sensor late-install thread (`doInstall`,
  `sensor_spoof.cpp:185`); reader `overlapsHideRange` (`:56-62`) chạy trên
  **mọi thread** qua `my_open`/`my_openat` từ `native_init`. Theo
  TSan-semantics đây là data race: write non-atomic `g_hideRanges[i]` +
  `g_hideRangeCount++` trong khi thread khác read non-atomic cùng lúc —
  reader có thể thấy count mới nhưng element chưa publish (torn read),
  tệ nhất là filter maps sai (lộ hoặc ẩn nhầm mapping).

## Root cause
Bảng hide-range được thiết kế như cấu trúc single-thread (eager phase của
`native_init`) nhưng sau B7 có thêm writer muộn trên thread khác
(`ensureSensorHookInstalled` → `doInstall`), trong khi reader đã luôn
multi-thread. Không có happens-before edge nào giữa element-write và
element-read.

## Fix
Publish protocol release/acquire, array giữ nguyên (append-only):
- `g_hideRangeCount` → `std::atomic<size_t>` (`maps_stealth.cpp`).
- Writer (`addHideRange`): `load(relaxed)` lấy slot → ghi element
  **trước** → `store(n + 1, release)` **sau**.
- Reader (`overlapsHideRange`, `hideRangeCount`): `load(acquire)`
  **trước** khi đọc elements.
- Phân tích writer-concurrency (quyết định không dùng `fetch_add`/lock):
  mọi `addHideRange` đều serialize — 3 writer eager (`installHooks`,
  `dl_iterate_phdr(collectSelfLibRanges, …)`, binder hook) chạy nối tiếp
  trên native_init thread (`jni_bridge.cpp:106-132`); writer muộn duy nhất
  (`doInstall`, `sensor_spoof.cpp:185`) chỉ chạy sau khi `native_init`
  return (trigger `on_library_loaded`/JNI) và tự serialize qua
  `g_installLock` CAS trong `ensureSensorHookInstalled`. Tại 1 thời điểm
  chỉ có đúng 1 writer → plain load+store + release/acquire là đủ;
  `fetch_add` không những thừa mà còn sai protocol (reserve slot trước,
  publish count trước khi element ghi xong).
- Comment trong code ghi rõ protocol + single-writer invariant (tiếng Anh,
  memory_order显式, khớp style file).

## Check (chạy được)
```sh
cd ~/workspace/SpoofX
# 1. Count là atomic, writer release / reader acquire:
grep -n 'atomic<size_t> g_hideRangeCount' \
  lsmodule/src/main/cpp/spoofx_native/maps_stealth.cpp
grep -n 'memory_order_release' lsmodule/src/main/cpp/spoofx_native/maps_stealth.cpp
# kỳ vọng: store(n + 1, release) trong addHideRange
grep -n -A3 'overlapsHideRange(uintptr_t' \
  lsmodule/src/main/cpp/spoofx_native/maps_stealth.cpp
# kỳ vọng: load(acquire) trước vòng for

# 2. Không còn plain access nào tới g_hideRangeCount:
grep -n 'g_hideRangeCount' lsmodule/src/main/cpp/spoofx_native/maps_stealth.cpp
# kỳ vọng: mọi dòng đều qua .load(...) / .store(...)

# 3. Xác nhận single-writer: liệt kê mọi writer:
grep -rn 'addHideRange(' lsmodule/src/main/cpp/spoofx_native/ --include=*.cpp \
  | grep -v 'void addHideRange'
# kỳ vọng: 4 call sites — 3 trong native_init thread (hook_install.cpp:236,
# collectSelfLibRanges via jni_bridge.cpp:110, jni_bridge.cpp:132) + 1 trong
# doInstall (sensor_spoof.cpp:185, serialize bởi g_installLock)

# 4. CI Android xanh trên commit landing (GitHub Actions).
# Ghi chú: TSan on-device không chạy được trong sandbox (xem TOOLS.md —
# build Android chỉ qua CI); verify bằng code inspection + CI build.
```
