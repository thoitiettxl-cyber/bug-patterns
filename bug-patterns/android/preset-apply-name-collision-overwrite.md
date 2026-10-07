# applyPreset() đặt tên theo label preset → ghi đè lặng lẽ profile trùng tên

- **Triệu chứng:** user apply một device preset vào profile mới; một profile
  khác có tên (sanitised) trùng với label preset biến mất/không còn dữ liệu
  cũ — không có cảnh báo nào. (SpoofX, 2026-10-02:
  `ProfileEditorViewModel.applyPreset()` gán
  `p.name = Profile.sanitiseName(preset.label)` không kiểm tra trùng.)
- **Root cause:** `ProfileRepository.save(edited, previousName)` key theo
  `Profile.name` (insert-or-replace), nên rename thành tên đã tồn tại =
  overwrite profile khác. `Profile.sanitiseName()` còn làm tăng xác suất
  va chạm (uppercase, space/dash/slash → `_`).
- **Fix:** trước khi gán, `repo.findByName(candidate)`; nếu đã tồn tại (trừ
  chính profile đang edit, so với `originalName`) thì sinh tên duy nhất bằng
  hậu tố số (`base`, `base_2`, `base_3`, …). `findByName` so sánh
  case-insensitive nên dedupe phủ luôn va chạm khác case. Giữ nguyên behavior
  khi tên không trùng.
- **Phòng (check chạy được):**
  `rg "\.name = .*sanitiseName" lsmodule/src/main/java --type kotlin` — mọi
  nơi gán tên từ sanitised label phải qua dedupe; review `save()` call site
  nào rename profile thì xác nhận không đè tên đã có.
