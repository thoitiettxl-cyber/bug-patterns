# Bulk revision bump: một lần cho mỗi entity, không phải mỗi dòng

## Triệu chứng
Operation bulk `confirmOrderLineCostCorrection` (146 dòng / 76 đơn) fail giữa chừng
với `REVISION_CONFLICT: Stale revision` — dù preview pass 146/146, 0 blocker.

## Root cause
Trong vòng lặp apply, code gọi `store.bump(order, expectedRevision)` cho **mỗi
correction**. Đơn có 2+ dòng lỗi → lần bump thứ 2 dùng revision đã cũ (lần 1 đã
tăng) → conflict. Ngoài ra `runInTransaction` ở cả `MemoryStore` lẫn
`LiveKvStore` đều **không rollback state khi work() throw** (chỉ so sánh
projection legacy) → fail giữa chừng = apply một phần âm thầm, token confirm
thì đã bị đánh `consumedAt`.

## Fix
Tách 3 phase trong confirm: (1) validate toàn bộ corrections trước,
(2) bump mỗi order **distinct** đúng 1 lần, (3) apply assignments.
Bump fail → chưa apply gì. Apply sau validate/bump không còn điểm fail.

```ts
const validated = corrections.map(...); // validate all first
const bumped = new Set<string>();
for (const { order, orderId } of validated) {
  if (bumped.has(orderId)) continue;
  this.store.bump(order, intent.expectedRevisions[orderId]);
  bumped.add(orderId);
}
// then apply
```

## Check phòng
- Mọi operation bulk có bump/fail: test **2+ items trên cùng 1 entity** trong 1 call
  (test regression: "applies several lines on the same order").
- Đừng assume transaction rollback — đọc `runInTransaction` thật; nếu không
  rollback thì confirm phải validate-hết-trước-apply.
- Token confirm bị consume ngay cả khi operation fail → retry luôn cần preview mới.
