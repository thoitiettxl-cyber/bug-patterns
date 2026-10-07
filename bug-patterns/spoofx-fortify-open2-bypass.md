# spoofx-fortify-open2-bypass — Dobby patch `open`/`openat` không bắt được caller fortified (`__open_2`/`__openat_2`)

## Triệu chứng
- Phát hiện qua audit (chiến dịch `spoofx-compliance-fix`, P1-5, 2026-10-06),
  không phải field incident: với `_FORTIFY_SOURCE=2` (NDK default), mọi
  native caller gọi `open(path, flags)` đều được compiler route sang symbol
  riêng `__open_2` / `__openat_2`. Hai symbol này gọi thẳng internal
  `__openat`, không đi qua public `open`/`openat` — nên Dobby inline-patch
  trên `"open"`/`"openat"` (`kHooks[]`, `hook_install.cpp`) **không bao giờ
  nổ** với caller fortified. Kết quả: maps-stealth + `/proc/version` spoof
  lặng lẽ tắt đối với đúng nhóm caller phổ biến nhất (mọi .so build bằng
  NDK mặc định). Không crash, không log — lỗ hổng coverage câm.

## Root cause
Giả định sai: "`open` là entry point duy nhất". Thực tế bionic tách 2 symbol
fortify riêng (verify trực tiếp AOSP 2026-10-06):
- `platform/bionic` main, `libc/bionic/open.cpp`
  (blob `bd8685a3ad8e294670c39725693bc903858a3150`):
  - L144: `int __open_2(const char* pathname, int flags)` — fortify-abort
    nếu `O_CREAT`/`O_TMPFILE` (L146), rồi gọi internal `__openat` trực tiếp
    (L148), không qua public `open`.
  - L182: `int __openat_2(int fd, const char* pathname, int flags)` —
    tương tự (L184/L186), không qua public `openat`.
- Public `open` (L116) / `openat` (L154) là function variadic riêng biệt.
  Patch prologue của chúng không chạm tới `__open_2`/`__openat_2`.
- URL citation:
  `https://android.googlesource.com/platform/bionic/+/main/libc/bionic/open.cpp`

## Fix
Thêm 2 entry optional vào `kHooks[]` (`hook_install.cpp`), sau entry
`openat`:
- `"__open_2"` → replacement `my_open`, `"__openat_2"` → `my_openat`,
  `critical: false` (không phải mọi libc đều export 2 symbol này; thiếu thì
  maps-stealth vẫn chạy cho caller non-fortified).
- Dùng chung replacement được vì ABI an toàn: `__open_2` không bao giờ nhận
  `O_CREAT` (fortify abort trước), nên `my_open` — chỉ `va_arg` khi
  `openNeedsMode(flags)` — không bao giờ đọc vararg không tồn tại. Tương tự
  `__openat_2` → `my_openat`.
- **Trampoline của 2 entry fortify KHÔNG publish vào `o_open`/`o_openat`
  (publish/clear là no-op có comment).** Lý do: route original-call qua
  trampoline `__open_2` sẽ chạy lại fortify check trên `flags` mà `my_open`
  nhận hợp lệ từ public `open` (vd open `O_CREAT` của caller non-fortified)
  → `__fortify_fatal` → abort process. `my_open`/`my_openat` luôn tới
  original code qua trampoline chuẩn của `open`/`openat`.
- Vòng install loop hiện có tự `addHideRange` cho trampoline page của 2 entry
  mới — không cần code thêm.
- `HOOK_MAP.md`: bổ sung 2 dòng `__open_2`/`__openat_2`.

## Check (chạy được)
```sh
cd ~/workspace/SpoofX
# 1. 2 entry tồn tại, đúng replacement, optional:
grep -n -A6 '"__open_2"' lsmodule/src/main/cpp/spoofx_native/hook_install.cpp
# kỳ vọng: (void *) my_open ... /* critical */ false
grep -n -A6 '"__openat_2"' lsmodule/src/main/cpp/spoofx_native/hook_install.cpp
# kỳ vọng: (void *) my_openat ... /* critical */ false

# 2. Trampoline fortify KHÔNG đè o_open/o_openat (kẻo fortify-abort):
grep -n -B2 -A8 'trampoline discarded' lsmodule/src/main/cpp/spoofx_native/hook_install.cpp
# kỳ vọng: publish lambda no-op + comment giải thích

# 3. Không đổi behavior open/openat hiện tại:
git diff --stat # chỉ thêm entry + comment, không sửa entry cũ

# 4. CI Android xanh trên commit landing (GitHub Actions).
```
