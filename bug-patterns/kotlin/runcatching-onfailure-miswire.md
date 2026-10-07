# Chèn code giữa runCatching và .onFailure → mất handler, log sai

- **Triệu chứng:** `runCatching { hookA() }` mất `.onFailure` → fail câm;
  `runCatching { hookB() }` có 2 `.onFailure` dòng sau log sai message của A.
  (SpoofX FakeGpsModule.kt:152-157, :172-175; batch H-P1-1 2026-10-05, review
  Phase 3 bắt được.)
- **Root cause:** Worker chèn block `runCatching { hookB() }` mới VÀO GIỮA
  `runCatching { hookA() }` và `.onFailure { ... "hookA failed" }` của nó.
  Kết quả: handler của A bị "móc" vào B (Kotlin chain theo vị trí, không theo
  tên), A không còn handler, B có 2 handler (1 đúng + 1 mang message của A).
- **Fix:** Mỗi `runCatching` phải đi kèm `.onFailure` ngay sau nó; khi chèn
  block mới, đặt TRỌN BỘ (runCatching + onFailure) không tách rời.
- **Check chạy được:** grep `runCatching` đếm số lượng, grep `.onFailure`
  đếm số lượng — 2 số phải bằng nhau; review diff: không bao giờ thấy 2
  `.onFailure` liên tiếp cho 1 `runCatching`.
