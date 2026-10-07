# Elvis dính liền sau if-else có nhánh return không narrow nullable

## Triệu chứng
CI `compileDebugKotlin` đỏ (run 37261849595):
```
e: FakeGpsModule.kt:532:15 Only safe (?.) or non-null asserted (!!.)
   calls are allowed on a nullable receiver of type 'Method?'.
```

## Root cause
```kotlin
val method = if (onSPlus) {
    resolveMethod(...)
} else if (cond) {
    resolveMethod(...)
} else {
    return          // nhánh else là return, không phải giá trị
} ?: return         // <-- dính liền: compiler KHÔNG narrow Method? -> Method
method.hookBefore { ... }  // lỗi: receiver vẫn Method?
```
Trong khi dạng `when` với `else -> <giá trị>` + `} ?: return` (dòng 348
cùng file) thì compile qua bình thường. Quy tắc rút ra: đừng bao giờ viết
`?: return` dính liền ngay sau if/when-expression mà một nhánh là `return`.

## Fix
Tách elvis thành statement riêng để smart cast chắc chắn:
```kotlin
val method: Method? = if (onSPlus) {
    ...
} else if (cond) {
    ...
} else {
    return
}
method ?: return
// từ đây method: Method (non-null), smart cast đảm bảo
```

## Phòng
- Grep `} ?: return` sau khi viết code lấy Method/lazy-init nullable —
  nếu nhánh else là `return`, tách dòng.
- Bài học quy trình (2026-10-05): sau mọi push, phải có người canh CI tới
  xanh/đỏ và fix ngay — campaign kết thúc ở commit mà không canh CI là
  thiếu acceptance.
