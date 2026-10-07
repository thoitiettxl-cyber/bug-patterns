# Docs đếm sai số native hook (D-P1-1)

- **Triệu chứng:** Docs đếm 5 native hook, code có 6 (`__system_property_foreach`
  thêm từ commit 6f672d4) + 1 ioctl hook. (SpoofX, audit 2026-10-05.)
- **Root cause:** Thêm entry vào `kHooks[]` mà không update 2 docs đếm số lượng.
- **Fix:** Thêm row `__system_property_foreach` vào bảng Native `HOOK_MAP.md`;
  "five" → "six" (+ "a sixth" → "a seventh" cho ioctl) trong `ARCHITECTURE.md`.
- **Check:** đếm entry `kHooks[]` trong `hook_install.cpp` == số row bảng Native
  == số bullet trong ARCHITECTURE.
