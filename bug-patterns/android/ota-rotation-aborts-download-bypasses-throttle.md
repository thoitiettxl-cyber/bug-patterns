# Xoay màn hình giữa OTA Downloading → abort câm + bypass throttle (U-P1-2)

- **Triệu chứng:** Xoay giữa `Downloading` → job chết câm (UI về `Idle`, progress
  mất); xoay sau khi check xong → `cachedCheck` mất → bấm "kiểm tra" bắn network
  ngay, bypass throttle 10 phút (`CHECK_THROTTLE_MS`). (SpoofX, audit 2026-10-05.)
- **Root cause:** `rememberCoroutineScope()` bị cancel khi composition recreate;
  mọi state (`uiState`, `cachedCheck`, progress) là plain `remember` nên reset
  về giá trị khởi tạo.
- **Fix:** `viewModelScope` (sống qua rotation) + `StateFlow` cho `uiState` /
  `progressRead` / `progressTotal` / `cachedCheck` trong `UpdateViewModel`;
  download tiếp tục chạy, composition mới re-collect progress; throttle giữ
  nguyên vì cache không mất. Dọn file dở: `OtaDownloader` đã xóa `.part` trên
  mọi nhánh failure; VM thêm `deleteStalePart` defense-in-depth trong
  `CancellationException` handler và `onCleared()`.
- **Check chạy được:** (1) `preflight-edit check` pass; (2) máy thật: xoay giữa
  `Downloading` → progress bar tiếp tục (không về `Idle`), tải xong báo
  `Downloaded`; (3) check xong → xoay → bấm "kiểm tra" → log
  `update check throttled — surfacing cached outcome`, không request network
  mới; (4) back giữa download → không còn file `.part` trong `cacheDir/ota/`.
