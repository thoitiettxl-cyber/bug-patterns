# Docs ghi sai cơ chế hook native (D-P1-2)

- **Triệu chứng:** README "six hooks via the libxposed Native API" vs
  ARCHITECTURE "five Dobby inline hooks" — mâu thuẫn nhau và sai cơ chế.
  (SpoofX, audit 2026-10-05.)
- **Root cause:** Nhầm lớp loading (libxposed `native_init` entry) với cơ chế
  hook (Dobby inline).
- **Fix:** Chốt theo code ở cả 2 file: `DobbyHook` gọi trực tiếp
  (`hook_install.cpp:200`, `binder_hook/dispatcher.cpp:1119`); libxposed Native
  API chỉ là module-loading layer (`native_init` tại `jni_bridge.cpp`).
- **Check:** grep `DobbyHook(` trong `lsmodule/src/main/cpp/` — mọi call site
  đều được docs phản ánh đúng cơ chế.
