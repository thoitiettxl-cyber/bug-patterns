# livedata-same-instance-skip-recompose

## Triệu chứng
Mọi control trong màn hình editor (Switch, TextField) "đơ": bật/tắt hoặc gõ chữ
không thấy UI đổi. Dữ liệu vẫn được ghi đúng vào object (save vẫn lưu được giá
trị mới) — chỉ UI không phản ánh. Dễ nhầm thành "callback bị đứt".

## Root cause
ViewModel mutate object tại chỗ rồi gán lại CHÍNH instance đó vào LiveData:

```kotlin
fun setToggle(t: ProfileToggle, on: Boolean) {
    val p = working.value ?: return
    p.setToggle(t, on)   // mutate tại chỗ
    working.value = p    // <-- same instance
}
```

Bridge LiveData→Compose (`LiveDataState.observeAsState`) dùng `mutableStateOf`
với `structuralEqualityPolicy()` mặc định. Model là `class` thường, không
override `equals` → `==` rơi về reference equality → cùng instance = "bằng
nhau" → Compose skip recomposition. UI controlled (`checked = ...`,
`value = ...`) kẹt ở giá trị cũ mãi mãi.

Port từ Fragment sang Compose hay mang theo pattern "working copy + LiveData"
mà không tính đến equality policy của Compose state.

## Fix
Publish bản copy sau mỗi lần mutate, để reference luôn mới:

```kotlin
working.value = Profile(p)   // deep-copy constructor
```

(Áp cho mọi setter publish `working`; KHÔNG đụng `save()`/`load()`.)

## Check phòng ngừa
```bash
# Setter nào gán lại cùng biến vừa mutate thì phải là bản copy:
rg -n 'working\.value = p\b' lsmodule/src/main/java --pcre2
# Model dùng trong Compose state mà không phải data class / không override
# equals + bị gán same-instance → nghi ngờ ngay.
```
