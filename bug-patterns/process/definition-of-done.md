# Definition of Done — checklist giao artifact Android

Trước khi giao APK/zip cho Boss, bắt buộc qua hết:

1. **Cold start:** nhập setting → kill process → mở lại → setting còn nguyên
   (chống `prefs-wipe-cold-start`).
2. **Reboot:** reboot máy → service/tính năng chạy nền có tự về không.
3. **Vuốt tắt:** vuốt khỏi recents → foreground service + overlay + tunnel có
   hồi sinh trong vài giây không (chống `swipe-kill`).
4. **Đúng máy Boss:** test trên OnePlus của Boss (hoặc đúng device target),
   không phải emulator/AOSP lý thuyết — OEM kill app khác nhau.
5. **Tắt tay:** tắt tính năng bằng toggle → vuốt tắt → phải tắt hẳn, không
   tự hồi sinh (chống restart mù).
6. **Không secret:** quét repo không có token/key thô
   (`grep -ri "token\|api[_-]key" --include="*.kt"` rà tay từng hit).
7. **Verify artifact:** revision trong file khớp commit CI, có chữ ký
   (xem `verify-artifact.md`).
8. **CI xanh** đúng run, đúng commit.

Thiếu mục nào → ghi rõ "chưa test mục X" khi giao, đừng im lặng.
