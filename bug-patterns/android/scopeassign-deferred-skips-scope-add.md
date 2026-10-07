# Bug Pattern: DEFERRED scope add bị skip vì return sớm

## Triệu chứng
`assignProfileWithScope` (lsmodule `ui/apps/ScopeAssign.kt`): khi remote prefs
chưa bind, `repo.assignPackage` commit local thành công, trả về status
`ProfileMutationStatus.DEFERRED`. UI toast "publication deferred" nhưng package
không bao giờ vào LSPosed scope list → module không inject vào process đó cho
tới khi user tự add scope thủ công. User chỉ thấy toast, không biết còn thiếu
scope.

## Root cause
Nhánh `DEFERRED` trong `when (assignment.status)` gọi `toast(...)` rồi
`return` ngay, trước cả khối `requestScopeBestEffort(appCtx, pkg)` ở dưới.
Có vẻ DEFERRED được copy từ các nhánh failure (BLOCKED_PINNED /
AMBIGUOUS_NAMES / PROFILE_NOT_FOUND / STORAGE_ERROR / INVALID_NAME) vốn
`return` đúng — nhưng DEFERRED là trạng thái "committed locally, publication
deferred" (`ProfileMutationResult.committed == true`), nên phải chạy tiếp phần
scope như APPLIED/UNCHANGED. Chỉ có reload broadcast + toast applied/detached
mới cần skip (vì `published == false`).

## Fix
Xóa `return` trong nhánh DEFERRED, giữ toast, để flow rơi xuống khối xử lý scope
chung:
- `profileName != null` → `requestScopeBestEffort(appCtx, pkg)` (fail-soft:
  no-op khi `xposedService == null`, try/catch khi gọi scope API).
- `profileName == null` → `removeScopeBestEffort` nếu không còn profile nào
  target package (check trên local state đã commit, vẫn đúng cho DEFERRED).
- Reload broadcast vẫn được skip bởi guard `status != APPLIED` sẵn có;
  toast applied/detached cũng không hiện.
- Comment trong code giải thích thứ tự: toast trước, scope sau; reconciler
  chỉ publish profile data, không bao giờ đụng scope.

## Check grep phòng ngừa
```bash
# Tìm return sớm trong nhánh DEFERRED của các when(status) khác —
# DEFERRED đã commit local nên không bao giờ được đối xử như failure.
rg -n "DEFERRED" --glob '*.kt' lsmodule/src | xargs -I{} sh -c 'echo "--- {}"'
rg -n -B2 -A2 'return' lsmodule/src/main/java/com/thoittxl/spoofx/ui/apps/ScopeAssign.kt
```
Quy tắc: trước khi thêm `return` trong một nhánh status, kiểm tra
`ProfileMutationResult.committed` — nếu nhánh đó `committed == true`, nhánh
phải chảy tiếp qua phần xử lý post-commit (scope, cache...), chỉ skip phần
đòi `published == true` (reload, applied toast).
