# `viewModel()` trần trong NavDisplay entry: miuix-nav bọc entry bằng NavEntryViewModelStoreOwner → rớt về NewInstanceFactory → crash

- **Triệu chứng:** mở ProfileEditorScreen là crash ngay khi compose,
  100% repro, logcat lặp từng frame
  `java.lang.RuntimeException: Cannot create an instance of class ak1`
  (ak1 = `ProfileEditorViewModel` sau R8). CI không bao giờ bắt vì CI
  không launch app. (SpoofX, 2026-10-01, miuix-nav 0.9.4-rc01.)
- **Root cause:** miuix-nav bọc mỗi NavDisplay entry trong
  `NavEntryViewModelStoreOwner` — class này chỉ implement
  `ViewModelStoreOwner`, KHÔNG implement
  `HasDefaultViewModelProviderFactory`. `viewModel()` của lifecycle
  runtime chỉ dùng `AndroidViewModelFactory` mặc định khi owner có
  `HasDefaultViewModelProviderFactory`; thiếu nó thì rớt về
  `NewInstanceFactory`, vốn đòi constructor không tham số.
  `ProfileEditorViewModel(app: Application)` chỉ có constructor
  `(Application)` → throw ngay trong `viewModel()` khi compose.
  Bẫy: code compile sạch, hoạt động ở màn hình không nằm trong NavDisplay
  (activity/Fragment owner có default factory), chỉ nổ ở entry của
  miuix-nav — nhìn như bug của screen chứ không phải của nav wrapper.
- **Fix:** không đổi DI, cấp factory explicit tại callsite
  (ProfileEditorScreen.kt):
  ```kotlin
  @Composable
  private fun rememberProfileEditorViewModelFactory(): ViewModelProvider.Factory {
      val app = LocalContext.current.applicationContext as Application
      return remember(app) {
          object : ViewModelProvider.Factory {
              @Suppress("UNCHECKED_CAST")
              override fun <T : ViewModel> create(modelClass: Class<T>): T {
                  if (modelClass.isAssignableFrom(ProfileEditorViewModel::class.java)) {
                      return ProfileEditorViewModel(app) as T
                  }
                  throw IllegalArgumentException("Unknown ViewModel class: $modelClass")
              }
          }
      }
  }
  ```
  và đổi default param thành
  `vm: ProfileEditorViewModel = viewModel(factory = rememberProfileEditorViewModelFactory())`.
  Giữ `remember(app)` để factory ổn định qua recomposition; branch
  `else` throw `IllegalArgumentException` thay vì fallback — fail loud
  nếu factory bị dùng nhầm cho class khác.
- **Phòng (check chạy được):**
  ```bash
  # repo-wide: mọi viewModel() trong NavDisplay entry phải kèm factory
  grep -rn "viewModel()" lsmodule/src/main/java/com/thoittxl/spoofx/ui/ \
    | grep -v "factory" # phải trống; hit nào = entry chưa fix
  # guard tương ứng: factory helper phải tồn tại ở mỗi hit của check trên
  grep -rln "ViewModelProvider.Factory" lsmodule/src/main/java/com/thoittxl/spoofx/ui/
  ```
  Quy tắc: **bất kỳ composable nào nằm trong NavDisplay entry mà gọi
  `viewModel()` cho ViewModel có constructor khác không-tham-số
  (đặc biệt `(Application)`) PHẢI truyền `factory` explicit** — đừng tin
  default factory của lifecycle runtime khi owner là wrapper của
  navigation lib.
