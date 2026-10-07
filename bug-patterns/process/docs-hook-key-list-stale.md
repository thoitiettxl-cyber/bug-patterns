# HOOK_MAP liệt kê thiếu keys/targets (D-P1-5, D-P1-6)

- **Triệu chứng:** `HOOK_MAP.md` row 1 liệt kê 3 keys trong khi code `KEYS` có 7;
  row 2 chỉ ghi `getInt` Global/System, thiếu `getString` + `NameValueCache`.
  (SpoofX, audit 2026-10-05.)
- **Root cause:** Module mở rộng (thêm keys, thêm lớp mask) mà docs row không
  update theo.
- **Fix:** Liệt kê đủ 7 keys (`DevOptionsHideModule.kt:99-107`) + cite; thêm
  `hookGetString` Global/System (`:31-35`) + `hookNameValueCache()` (`:35`)
  cho AirplaneMode.
- **Check:** đọc `install()` của module, liệt kê mọi entry point bị hook, đối
  chiếu docs — mỗi điểm trong code đều có trong docs.
