# Stats/header nhét vào `LazyColumn` → "dải trắng" scroll theo list (SpoofX Profiles)

- **Triệu chứng:** màn hình Profiles (SpoofX) xuất hiện "dải trắng" lạ dưới
  dòng "71 hồ sơ": hai thẻ trắng (`surfaceContainer = #FFFFFF` trong miuix
  `lightColorScheme`) trên nền app `#F5F5F5`, cao ~78dp + spacer 12dp ≈ 102dp,
  nằm giữa search bar và list. Cuộn list thì dải này cũng cuộn theo
  (2026-10-01).
- **Root cause:** bản legacy (`fragment_profiles.xml` @ `df3f11c^`) giữ thứ tự
  **stats → search → list**, và stats + search **cố định ngoài RecyclerView**
  (comment trong XML: "kept flat on purpose so the list scroll does not also
  scroll the stats off-screen"). Bản rewrite Compose đảo thứ tự thành
  search → stats → list và nhét cả ba vào cùng một `LazyColumn` dưới dạng
  `item { ... }` + `Spacer(12.dp)` — nên header trắng scroll chung với list và
  padding của item tạo ra "dải" nhìn như bug.
- **Fix (Option B — đã chốt, `ProfilesScreen.kt`):** đưa `StatsRow` +
  `SearchBar` ra khỏi `LazyColumn`, thành `Column` header cố định phía trên;
  chỉ list hồ sơ scroll. Thứ tự header: StatsRow trước, SearchBar sau (khớp
  bản cũ). Xóa `item { SearchBar(...) }`, `item { StatsRow(...) }` và 2
  `Spacer(12.dp)` khỏi LazyColumn; bỏ `contentPadding` top cũ của LazyColumn
  (giữ `bottom = bottomPadding`), LazyColumn dùng `weight(1f)` để fill phần
  còn lại. Thêm `modifier: Modifier = Modifier` cho `StatsRow` để gắn
  `padding(top = 12.dp)` — không đổi màu, không đổi logic search/filter.
  ```kotlin
  Column(modifier = Modifier.fillMaxSize()) {
      StatsRow(total = currentList.size, active = activeCount,
               modifier = Modifier.padding(top = 12.dp))
      SearchBar(searchStatus = searchStatus,
                onSearchStatusChange = { searchStatus = it })
      LazyColumn(
          modifier = Modifier.fillMaxWidth().weight(1f)
              .scrollEndHaptic().overScrollVertical(),
          contentPadding = PaddingValues(bottom = bottomPadding),
      ) {
          // ... chỉ items của list
      }
  }
  ```
- **Phòng (check chạy được):**
  ```bash
  # header cố định (stats/search/filter bar) không được nằm trong LazyColumn dưới dạng item:
  grep -n "item {" \
    lsmodule/src/main/java/com/thoittxl/spoofx/ui/screen/main/ProfilesScreen.kt
  # mọi item còn lại trong LazyColumn phải là row của list (EmptyState / groupedCardItems / spacer cuối)
  # invariant: không có item { SearchBar / StatsRow } nào bên trong block LazyColumn
  ```
  Quy tắc: cái gì cố định trên màn hình (stats, search, filter) thì nằm NGOÀI
  `LazyColumn`, theo thứ tự bản legacy; chỉ dữ liệu list mới là `item`.
  Nếu header phải scroll cùng list thì mới để trong LazyColumn — và phải ghi
  rõ ý đồ trong comment.
