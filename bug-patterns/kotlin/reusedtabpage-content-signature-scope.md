# Truy cập biến wrapper từ content lambda → unresolved reference (compile break)

## Triệu chứng
`MainActivity.kt:355,381,392`: `unresolved reference: scrollBehavior` —
`ReusedTabPage(...) { topPadding -> HomeScreen(..., scrollBehavior =
scrollBehavior) }` không compile. Worker tưởng "truyền đúng instance"
nhưng sai ở dạng nặng hơn: không build nổi.

## Root cause
`val scrollBehavior = MiuixScrollBehavior()` chỉ tồn tại trong body của
`ReusedTabPage`; các call site viết content lambda tại `AppNavigation` —
lexical scope khác, Kotlin không có dynamic scope. `content:
@Composable (Dp) -> Unit` không expose behavior ra ngoài.

## Fix
Đổi signature `content` thành `@Composable (topPadding: Dp,
scrollBehavior: ScrollBehavior) -> Unit`; trong body gọi
`content(innerPadding.calculateTopPadding(), scrollBehavior)`; call site
nhận `{ topPadding, scrollBehavior -> ... }`. Verify bằng grep: mọi
occurrence của `scrollBehavior` đều được bind (lambda param / local val /
named-arg), không còn reference treo.

## Check chạy được
- CI `compileDebugKotlin`/`assembleRelease` xanh (lỗi này chỉ CI bắt được —
  AGENTS.md cấm Gradle local nên review tĩnh phải đọc scope kỹ).
- Phòng: khi truyền object của wrapper xuống content lambda, luôn đi qua
  param tường minh — không bao giờ reference biến trong lexical scope khác.
  Reviewer phải check "biến này khai báo ở scope nào, dùng ở scope nào".
