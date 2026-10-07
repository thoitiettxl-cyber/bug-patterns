# Link "Mã nguồn" trong Settings trỏ repo sai → GitHub 404

- **Triệu chứng:** bấm "Mã nguồn" trong tab Cài đặt mở browser ra trang
  GitHub 404. (SpoofX, 2026-10-01: `SOURCE_URL` =
  `https://github.com/thoitiettxl-cyber/Atexit-spm-injec_m` — tên repo cũ/bị
  biến dạng, không tồn tại.)
- **Root cause:** URL hard-code trong `SettingsScreen.kt` không được cập nhật
  khi repo đổi tên/di dời; không có test hay check nào bắt. (Lưu ý khi
  verify: repo `thoitiettxl-cyber/SpoofX` là PRIVATE nên fetch ẩn danh cũng
  404 — phải đối chiếu bằng `gh repo view` đã authenticate, hoặc mở trên
  máy có đăng nhập GitHub.)
- **Fix (SpoofX `cf7c8f8`):** `SOURCE_URL` →
  `https://github.com/thoitiettxl-cyber/SpoofX`. Bonus cùng batch:
  `openUrl()` trước đây `catch` im lặng — giờ show toast
  `settings_open_link_failed` khi không mở được link.
- **Phòng (check chạy được):**
  ```bash
  # mọi URL http(s) hard-code trong source phải fetch được 200:
  grep -rhoE "https?://[^\"' ]+" --include=*.kt lsmodule/src/main/java/com/thoittxl/spoofx/ui | sort -u
  ```
  Quy tắc: URL ngoài hard-code trong UI phải có trong checklist review khi
  rename repo; link chết là bug logic, không phải "sau này sửa".
