# eglCreateWindowSurface fail vì dùng 2 EGLConfig khác nhau cho context và window

- **Triệu chứng:** `eglCreateWindowSurface` trả `EGL_NO_SURFACE` liên tục trên
  máy thật (logcat: `eglCreateWindowSurface failed`), dù `eglChooseConfig`
  với `EGL_WINDOW_BIT` vẫn chọn được config. Preview đen, pipeline YUV không
  bao giờ chạy. (Camera2Magit libcamera3 rewrite, commit `a581077`.)
- **Root cause:** `initEGL()` chọn config `EGL_PBUFFER_BIT`-only cho context +
  pbuffer, rồi render loop gọi `eglChooseConfig` lần 2 với `EGL_WINDOW_BIT`
  cho window surface. Binary gốc (disassembly `initEGL @ 0x14253c`) chỉ dùng
  **một** config `EGL_WINDOW_BIT` duy nhất (lưu ở `this+0x1c8`) cho context,
  pbuffer **và** mọi window surface — Android EGL driver kén khi config của
  surface khác config đã dùng tạo context/pbuffer.
- **Fix:** một config chung `{R8G8B8A8, ES3, WINDOW_BIT}` lưu thành member;
  `addRenderTarget` tạo window surface **ngay** (eager, trên caller thread)
  như bản gốc, không tạo lazy trong render loop; render loop chỉ dùng surface
  đã tạo sẵn, `eglMakeCurrent` fail thì log `eglGetError()` + fallback về
  pbuffer. (Camera2Magit commit `8d4d43b`.)
- **Phòng:** khi viết lại code EGL từ binary, decode **nguyên** attribute list
  của `eglChooseConfig` trong `initEGL` (từng cặp attr/value trên stack) rồi
  mới quyết định config — đừng "hợp lý hoá" thành pbuffer-only vì thấy có
  `eglCreatePbufferSurface`. Check grep: `EGL_PBUFFER_BIT` trong file có
  `eglCreateWindowSurface` → nghi ngay.
- **Nguồn:** Camera2Magit `app/src/main/cpp/Camera3.cpp`, phát hiện qua logcat
  trên máy Boss (OnePlus, Android 16) + đối chiếu disassembly.
