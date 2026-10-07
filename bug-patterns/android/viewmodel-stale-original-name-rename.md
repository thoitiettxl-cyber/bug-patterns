# Ghost profile khi rename 2 lần liên tiếp không rời editor (stale originalName)

## Triệu chứng
Trong profile editor: đổi tên profile A → "B", bấm Save (OK), đổi tiếp "B"
→ "C", bấm Save. Kết quả: entry "B" vẫn còn trên disk (ghost), profile "C"
được tạo mới; package assignment có thể trôi sang entry cũ. Phải thoát editor
mở lại thì rename mới đúng.

## Root cause
`ProfileEditorViewModel` giữ `originalName` để truyền làm `previousName` cho
`ProfileRepository.save(edited, previousName)` — repo dùng nó để xóa key cũ
khi rename. Nhưng `originalName` chỉ được set một lần trong `load()` và
**không bao giờ cập nhật sau `save()` thành công**:

```kotlin
fun save(): ProfileMutationResult {
    val p = working.value ?: return ...
    return repo.save(p, originalName) // originalName vẫn là tên PRE-edit lần đầu
}
```

Lần save thứ 2 (rename "B" → "C") truyền `previousName = "A"` — key "A" không
còn tồn tại, nên repo không xóa được entry "B" → ghost. Đồng thời package
assignment cho owner cũ không được dọn đúng.

Vụ thật: `ProfileEditorViewModel.kt`, `originalName` stale sau save lần 1.

## Fix
Sau `repo.save` trả về status thành công, gán `originalName` bằng đúng tên
mà repo vừa dùng làm key lưu trữ. Repo lưu entry dưới `edited.name` (dùng
trực tiếp cho prefix `PACKAGES_PREFIX + edited.name` và cho
`claimPackages(owner = edited.name)` — không sanitize lại bên trong save),
nên:

```kotlin
fun save(): ProfileMutationResult {
    val p = working.value
        ?: return ProfileMutationResult(ProfileMutationStatus.STORAGE_ERROR)
    val result = repo.save(p, originalName)
    // Cập nhật sau save thành công để lần rename tiếp theo truyền
    // previousName đúng — không còn ghost entry, không mất package assignment.
    if (result.committed) {
        originalName = p.name
    }
    return result
}
```

`result.committed` = APPLIED / DEFERRED / UNCHANGED — chỉ cập nhật khi disk
đã thực sự nhận entry mới; các status lỗi (INVALID_NAME, BLOCKED_PINNED,
AMBIGUOUS_NAMES, STORAGE_ERROR) giữ nguyên `originalName` cũ để lần save
sau vẫn trỏ đúng entry trên disk.

## Check phòng ngừa
```bash
# Mọi ViewModel/Fragment truyền "previous name" vào repo.save:
rg -n 'repo\.save\(' --type kotlin lsmodule/src/main/java/ -B5 | rg -n 'previousName|originalName'
# Với mỗi hit: sau save thành công, biến "previous/original name" có được
# đồng bộ với tên vừa lưu không? Nếu không → rename lần 2 trong cùng session
# sẽ để lại ghost entry.
```
Luật: bất kỳ trường nào lưu "tên cũ" để phục vụ rename đều phải được refresh
ngay sau save thành công, trong cùng hàm gọi `repo.save`.
