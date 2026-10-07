# Public property expose internal type → lỗi compile (không cần explicit API mode)

- **Triệu chứng:** `public class UpdateViewModel : ViewModel()` có
  `val uiState: StateFlow<UpdateUiState>` trong đó `UpdateUiState` là
  `internal` → kotlinc báo lỗi "'public' property exposes its 'internal'
  type". (SpoofX UpdateScreen.kt, review Phase 3 2026-10-05 bắt P0.)
- **Root cause:** Đoán "không bật explicit API mode thì internal ở vị trí
  public vẫn compile được" — SAI. Kotlin luôn báo lỗi này (error, không phải
  warning), không liên quan explicit API mode. Đổi `private` → `internal`
  không giải quyết gì vì vấn đề là public API expose internal type.
- **Fix:** Bỏ `internal` ở type (thành public) HOẶC hạ cả class + property
  xuống `internal`. Nếu ViewModel cần public ctor cho NewInstanceFactory
  reflection thì chọn public type.
- **Check chạy được:** không compile local được (sandbox) → review checklist:
  mọi type xuất hiện trong public/protected signature phải public; grep
  `^internal (class|interface|data class)` rồi kiểm tra có bị expose không.
