# Cover-fit sai trục khi viết lại công thức aspect từ binary

- **Triệu chứng:** đường YUV overwrite (algorithm mode) cho ảnh méo/kéo dãn
  sai — frame 16:9 ra output 4:3 bị zoom ngang thay vì crop dọc. Preview EGL
  vẫn đúng nên khó phát hiện nếu chỉ test preview. (Camera2Magit libcamera3
  rewrite, `Camera3::processFrameToYUV`, commit `a581077`.)
- **Root cause:** khi viết lại từ disassembly, điều kiện chọn trục crop bị
  "hợp lý hoá" thành `if (1.0f <= s2)` (so output aspect với 1.0) trong khi
  binary gốc so **hai aspect với nhau**: `if (fVar5 < fVar4)` tức
  `if (s2 < s1)` — kiểm chứng ở cả logic inline trong
  `processFrameToYUV @ 0x1429b8` lẫn hàm độc lập `calculateYuv @ 0x142f7c`.
  Hai điều kiện chỉ trùng nhau khi frame aspect = 1.0 (hầu như không bao giờ).
  Đường preview (`processFrameToPreview`) viết đúng nên càng dễ chủ quan.
- **Fix:** `if (s1 <= s2) { s8 = s1/s2; s9 = 1; } else { s8 = 1; s9 = s2/s1; }`
  (tương đương `if (s2 < s1)` của gốc; tại s1 == s2 cả hai nhánh đều ra 1,1).
  (Camera2Magit dev-next, 2026-10-01.)
- **Phòng:** khi port công thức số học từ decompile, map từng biến float về
  đúng định danh gốc (s1 = frame aspect, s2 = output aspect) rồi dịch điều
  kiện **từng toán hạng**, đừng thay bằng hằng số "trông hợp lý". Nếu binary
  có 2 nơi implement cùng công thức (inline + hàm riêng) thì đối chiếu cả hai
  — chúng là oracle chéo cho nhau. Check grep: comment "matches the original
  binary exactly" mà không ghi địa chỉ hàm + offset so sánh → nghi ngay.
- **Nguồn:** Camera2Magit `app/src/main/cpp/Camera3.cpp::processFrameToYUV`
  đối chiếu `libcamera3.so_decompiled.c` (`processFrameToYUV @ 001429b8`,
  `calculateYuv @ 00142f7c`).
