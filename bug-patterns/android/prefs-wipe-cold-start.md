# Wipe prefs ngay lần cold start đầu tiên

- **Triệu chứng:** Thoát app mở lại → API key / token / hostname đã lưu bị mất
  sạch. (E-Muse, Boss báo 2026-09-30.)
- **Root cause (2 lỗi cộng hưởng):**
  1. `TextFieldState` tạo rỗng trong `Activity.onCreate()`, không seed từ
     `Prefs` — UI hiện ô trống dù prefs có dữ liệu.
  2. `LaunchedEffect(selectedTab)` persist 3 chuỗi rỗng ngay lần compose đầu
     (tab 0) → mỗi cold start ghi đè prefs bằng rỗng = tự wipe dữ liệu.
  3. Thoát app khi đang ở tab Cài đặt thì không có persist nào chạy (persist
     cũ gắn với chuyển tab).
- **Fix (E-Muse `3421ae9`):** seed state trực tiếp từ `Prefs` trong `onCreate`;
  persist trong `Activity.onPause()`; xóa persist theo tab-switch.
- **Phòng (check chạy được):**
  - Luật: **state hiển thị setting nào thì khởi tạo từ prefs đó, không bao giờ
    khởi tạo rỗng rồi persist ngược.**
  - Persist gắn với lifecycle (`onPause`/`onStop`), không gắn với UI event
    (chuyển tab, recompose).
  - Checklist tay khi test: nhập setting → kill process → mở lại → setting
    còn nguyên (nằm trong `definition-of-done.md`).
- **Nguồn:** E-Muse commit `3421ae9`, 2026-09-30.
