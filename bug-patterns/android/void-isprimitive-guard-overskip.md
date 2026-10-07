# void.class.isPrimitive() == true → guard skip nhầm method void

- **Triệu chứng:** Guard `if (method.returnType.isPrimitive) return@hookBefore`
  (định skip method trả primitive để tránh unbox NPE khi gán null) lại skip
  cả method `void` → original chạy → mất tác dụng chặn. (SpoofX
  FacebookAdsRemoverModule.kt, gate Phase 4 2026-10-05 BLOCK.)
- **Root cause:** `void.class.isPrimitive()` trả về `true` (void là 1 trong 9
  predefined Class objects). Nhưng `param.result = null` với method void VỪA
  an toàn (không unbox) VỪA chính là cơ chế chặn original. Spec và reviewer
  đều miss vì chỉ nhớ "isPrimitive cover void" mà không suy ra hệ quả ngược.
- **Fix:** `if (returnType.isPrimitive && returnType != Void.TYPE)`.
  Bảng chân lý: void → đi tiếp (bị null chặn); int/boolean/... → skip
  fail-open; reference type → đi tiếp.
- **Check chạy được:** grep guard dùng `isPrimitive` không kèm `Void.TYPE`;
  review checklist: mỗi lần viết guard isPrimitive phải hỏi "void thì sao?".
