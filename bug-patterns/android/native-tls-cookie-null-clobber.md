# Native TLS: cookie NULL bị drop + clobber outer call (H-P1-3)

- **Triệu chứng:** Callback hợp lệ với cookie NULL không bao giờ được gọi (mất dữ
  liệu thầm lặng); nested call cookie-NULL reset `tl_callback` → đầu độc outer
  call in-flight cùng thread. (SpoofX `property_hooks.cpp`, audit 2026-10-05.)
- **Root cause:** `my_callback` guard `!cookie` drop callback hợp lệ (bionic cho
  phép cookie opaque NULL); `my_system_property_read_callback` reset mù
  `tl_callback = nullptr` sau mỗi call thay vì save/restore.
- **Fix:** Bỏ `!cookie` khỏi guard (NULL cookie pass-through, callback vẫn fire);
  stash callback không yêu cầu cookie; save/restore TLS theo stack discipline
  (nested re-entrant call không clobber outer).
- **Check chạy được:** native/host test gọi `__system_property_read_callback` với
  cookie NULL → callback vẫn fire với cookie NULL; nested call (callback gọi
  read_callback khác với cookie NULL) → outer callback vẫn nhận đủ, TLS sau call
  ngoài = giá trị ban đầu.
