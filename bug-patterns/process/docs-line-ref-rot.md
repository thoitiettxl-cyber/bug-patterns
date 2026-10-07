# Line ref + cross-ref chết trong docs (D-P1-7)

- **Triệu chứng:** `HOOK_MAP.md` line ref "lines 119-140" sai (thực tế
  `GPHOTO_LABEL` ở `DevicePreset.kt:211`, entry `:229-232`); cross-ref
  "T2 Option A in ROADMAP.md" chết (0 hit). (SpoofX, audit 2026-10-05.)
- **Root cause:** Code di chuyển, ROADMAP viết lại; docs giữ ref cũ.
- **Fix:** Ref đúng đã verify + gỡ cross-ref chết.
- **Check:** verify mọi `file:line` trong docs bằng grep trước khi commit docs;
  grep cross-ref target tồn tại. (Bài học pass 1: đừng copy audit verbatim —
  reviewer bắt được line ref sai do copy.)
