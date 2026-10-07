# Dùng nhầm api làm workMode khi port render loop từ binary

- **Triệu chứng:** preview bị xoay/lật sai chỉ trong một số case rất hẹp
  (Camera1 + target portrait + display orientation 90/270) — còn lại trông
  bình thường nên dễ lọt qua test. (Camera2Magit libcamera3 rewrite,
  `Camera3::processFrameToPreview`, commit `a581077`.)
- **Root cause:** khi viết lại từ disassembly, thấy `processFrameToPreview`
  đọc một int từ `[this+0x0]` rồi dùng để chọn swap trục target
  (`w8 = workMode==0 ? tw : th`), đã "hợp lý hoá" thành `workMode = api_`
  (vì api cũng là int 1/2). Nhưng render loop gốc (`@0x41808`) **tính
  workMode riêng cho từng target trước khi gọi**: `0` mặc định, chỉ `1`/`2`
  khi đồng thời `targetW < targetH` && `api == 1` (Camera1) &&
  `displayOri % 180 == 90` (`1` = front, `2` = rear qua `this[0x84]`);
  rồi store vào `this+0x0`. Với Camera2, api_ = 2 làm mọi target bị swap
  trục sai; với Camera1 landscape cũng sai.
- **Fix:** tính workMode ở render loop theo đúng điều kiện gốc và truyền vào
  `processFrameToPreview` qua tham số (không đọc `api_` nữa; không cần giữ
  field `this+0x0` vì chỉ là biến tạm nội bộ của gốc).
  (Camera2Magit dev-next, 2026-10-01.)
- **Phòng:** khi một hàm đọc field `this+N` mà N nhỏ (0x0, 0x8, ...) thì tra
  ngược xem **ai ghi** vào đó trong caller — đừng gán nghĩa từ tên field
  của mình. Ghidra decompile thường hiện `*(undefined4 *)this = uVar7`
  ngay trước call site; đó là manh mối workMode được tính bên ngoài.
  Check grep: comment "api doubles as the work mode" không kèm địa chỉ
  verify → nghi ngay.
- **Nguồn:** Camera2Magit `app/src/main/cpp/Camera3.cpp::renderLoop` đối
  chiếu `libcamera3.so_decompiled.c` (render loop `@0x41808`, đoạn tính
  `uVar7` từ `this+0x80`/`this+0x8c`/`this[0x84]`).
