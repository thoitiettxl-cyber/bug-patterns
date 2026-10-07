# TabRow + `when (selectedTab)` one-way → vuốt không đổi tab; ScrollBehavior tạo mà không attach thì chết

- **Triệu chứng:** (1) `TabRow` trong ProfileEditorScreen chỉ đổi tab khi
  tap; vuốt ngang không chuyển tab dù có 5 tab. (2) App bar ở MainScreen
  không collapse khi cuộn nội dung bên dưới. (3) Ba màn hình con
  (Profiles/Apps/Settings) mỗi màn tự tạo một `MiuixScrollBehavior` local
  nhưng cuộn lên cuộn xuống không ảnh hưởng app bar nào. (SpoofX,
  2026-10-01, miuix-kt 0.9.4-rc01.)
- **Root cause:** (1) `TabRow(selectedTabIndex = selectedTab,
  onTabSelected = { selectedTab = it })` + `when (selectedTab) { ... }`
  là one-way binding: `selectedTab` chỉ đổi qua tap. Không có
  `PagerState` thì swipe gesture không có gì để drive và không có gì để
  lắng nghe → vuốt là no-op. (2) Compose nested scroll chỉ hoạt động khi
  `Modifier.nestedScroll(connection)` được attach vào layout BAO QUANH
  scrollable: tạo `MiuixScrollBehavior` rồi truyền vào
  `AdaptiveTopAppBar(scrollBehavior = ...)` nhưng không attach
  `nestedScrollConnection` vào đâu thì behavior mãi ở trạng thái idle,
  app bar không bao giờ nhận scroll delta → không collapse. (3) Copy-paste
  `scrollBehavior` từ TabHost vào từng tab con, nhưng app bar DUY NHẤT nằm
  ở TabHost (MainScreen): 3 behavior local không có consumer nào, state
  chết, scroll event còn bị nuốt vào connection không ai đọc.
- **Fix:**
  1. `val pagerState = rememberPagerState(initialPage = selectedTab,
     pageCount = { tabs.size })`; `LaunchedEffect(pagerState.currentPage)`
     sync một chiều pager → `selectedTab` (giữ `selectedTab` làm source of
     truth cho TabRow); helper `selectTab(index)` set `selectedTab` +
     `scope.launch { pagerState.animateScrollToPage(index) }` cho mọi đổi
     tab programmatic (tap qua `onTabSelected`, jump validation như
     `attemptSave()` → `TAB_DEVICE`); `when (selectedTab)` → 
     `HorizontalPager(state = pagerState) { page -> when (page) { ... } }`
     giữ nguyên 5 nhánh. Pager nằm TRONG `Column` dưới TabRow nên dùng
     `Modifier.weight(1f)` (fillMaxSize sẽ overflow Column, đáy tab bị
     cắt).
  2. `.nestedScroll(scrollBehavior.nestedScrollConnection)` attach vào
     `Scaffold` modifier của TabHost — đúng MỘT chỗ, nơi chứa cả app bar
     lẫn nội dung cuộn.
  3. Xóa 3 `MiuixScrollBehavior` local + `.nestedScroll(...)` của chúng ở
     Profiles/Apps/Settings; scroll của tab con dispatch lên cây và được
     behavior của TabHost consume. Xóa import thừa theo
     (splineBasedDecay, spring, nestedScroll, LocalDensity,
     MiuixScrollBehavior, rememberTopAppBarState) — chỉ xóa import nào
     grep không còn hit.
- **Phòng (check chạy được):**
  ```bash
  # mỗi MiuixScrollBehavior được tạo phải có đúng 1 chỗ attach connection:
  grep -rn "MiuixScrollBehavior(" lsmodule/src/main --include=*.kt
  grep -rn "nestedScrollConnection" lsmodule/src/main --include=*.kt
  # TabRow đi kèm pager thì phải có cả 2 chiều sync:
  grep -rn "TabRow(" lsmodule/src/main --include=*.kt | while read -r l; do :; done
  # trong file có TabRow + HorizontalPager: phải thấy cả
  # LaunchedEffect(pagerState.currentPage) và animateScrollToPage
  ```
  Quy tắc: `TabRow` + nội dung `when (selectedTab)` mà không có
  `PagerState` = vuốt chết — luôn đi kèm `HorizontalPager` +
  `rememberPagerState` + sync 2 chiều (pager→tab qua `LaunchedEffect`,
  tab→pager qua `animateScrollToPage`, kể cả các chỗ set tab bằng code
  như validation jump). `ScrollBehavior` tạo ở file nào thì
  `nestedScroll(connection)` phải attach ở layout chứa app bar của đúng
  file đó; behavior ở màn hình con không sở hữu app bar là dead code.

## Lesson phụ (2026-10-01, review diff trong chiến dịch)
- Khi nhiều worker cùng sửa một file (SettingsScreen.kt), chỉ dùng
  `muse.edit` với `old_text` tối thiểu khớp khít vùng mình sở hữu; edit
  fail thì đọc lại đoạn file rồi thử lại, không force. Diff của worker
  khác (KDoc/setTheme/runActivation) nằm vùng khác thì để yên tuyệt đối.
- Không build Android được trong sandbox → validate bằng đọc kỹ:
  import còn dùng không (grep), ngoặc cân (script đếm), và check layout
  semantics (pager trong Column phải `weight`, không `fillMaxSize`).
