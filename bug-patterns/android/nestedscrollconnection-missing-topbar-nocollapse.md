# Thiếu nestedScrollConnection → top bar không collapse

## Triệu chứng
4 màn hình (Home, Scope, Settings, Profiles) top bar không collapse khi
cuộn, trong khi 6 màn hình khác collapse bình thường.

## Root cause
`MiuixScrollBehavior` được tạo trong wrapper (`ReusedTabPage` /
`ProfilesSubPage` ở `MainActivity.kt` — chủ của top bar) nhưng 4 screen
không gắn `.nestedScroll(scrollBehavior.nestedScrollConnection)` vào
LazyColumn chính. Behavior phải là đúng instance của wrapper (tự tạo
behavior riêng trong screen thì bar vẫn không collapse vì sai instance).

## Fix
- Screen nhận thêm param `scrollBehavior: ScrollBehavior`, gắn
  `.nestedScroll(scrollBehavior.nestedScrollConnection)` vào LazyColumn
  (pattern từ `ThemeSettingsScreen.kt:209`).
- Wrapper truyền behavior của nó xuống: với `ReusedTabPage`, đổi signature
  `content` thành `(topPadding: Dp, scrollBehavior: ScrollBehavior) -> Unit`
  rồi truyền tại call site (không reference biến ngoài lexical scope —
  xem pattern `reusedtabpage-content-signature-scope.md`).

## Check chạy được
- CI `assembleRelease` xanh.
- Máy thật: cuộn 4 màn hình → top bar collapse/expand như 6 màn hình mẫu.
- Phòng: thêm màn hình mới trong wrapper có top bar → copy pattern
  param + nestedScroll ngay từ đầu; checklist "screen nào chưa gắn".
