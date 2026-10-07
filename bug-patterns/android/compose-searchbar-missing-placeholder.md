# SearchBar custom `decorationBox` thiếu placeholder → ô search trống trơn như "dải trắng lạ"

- **Triệu chứng:** ô search trong `ProfilesScreen`/`AppsScreen` (SpoofX) lúc
  chưa nhập gì chỉ hiện icon kính lúp trên nền `surfaceContainerHigh` bo tròn —
  không có gợi ý chữ nào, nhìn như một "dải trắng lạ"/layout bị thiếu. Màn
  hình nào dùng chung `SearchBar` đều bị giống hệt (2026-10-01).
- **Root cause:** `SearchBar` dùng `BasicTextField` với `decorationBox` tự vẽ
  tay (Row: icon search + `Box { innerTextField() }` + nút clear), KHÔNG dùng
  `placeholder` param của Material `TextField` — nên việc render hint phải do
  mình làm, và code gốc quên vẽ nó. `SearchStatus.label` đã tồn tại (được set
  ở mọi call site: `R.string.apps_search_hint`, `R.string.assign_profile_search_hint`…)
  nhưng không nơi nào trong `decorationBox` dùng tới → label chết.
- **Fix (1 chỗ, sửa cả 3 call site vì dùng chung composable):** vẽ `Text`
  placeholder *chồng lên* `innerTextField()` trong `Box`, chỉ khi
  `textFieldValue.text.isEmpty()`; style trùng chữ nhập (`17.sp`,
  `FontWeight.Medium`) nhưng màu mờ hơn — `colorScheme.onSurfaceVariantSummary`
  (màu secondary-text của Miuix, đã dùng ở nơi khác trong codebase),
  `maxLines = 1` để không vỡ layout khi label dài.
  ```kotlin
  Box(modifier = Modifier.weight(1f)) {
      if (textFieldValue.text.isEmpty()) {
          Text(
              text = searchStatus.label,
              fontSize = 17.sp,
              fontWeight = FontWeight.Medium,
              color = colorScheme.onSurfaceVariantSummary,
              maxLines = 1,
          )
      }
      innerTextField()
  }
  ```
- **Phòng (check chạy được):**
  ```bash
  # mọi BasicTextField có decorationBox tự vẽ mà không có placeholder -> rà soát:
  grep -rn "decorationBox" lsmodule/src/main --include=*.kt
  # mỗi decorationBox phải có nhánh vẽ hint khi value rỗng, hoặc dùng TextField.placeholder
  # invariant: SearchBar.kt phải chứa textFieldValue.text.isEmpty() đi kèm Text(...)
  grep -n "textFieldValue.text.isEmpty()" \
    lsmodule/src/main/java/com/thoittxl/spoofx/ui/component/SearchBar.kt # phải có hit
  ```
  Quy tắc: dùng `BasicTextField` + `decorationBox` custom = tự chịu trách nhiệm
  vẽ placeholder — không có param `placeholder` tự động như Material `TextField`.
  Màu hint lấy từ `colorScheme` của theme đang dùng (Miuix:
  `onSurfaceVariantSummary`), style copy từ `textStyle` của field để baseline
  không lệch.
