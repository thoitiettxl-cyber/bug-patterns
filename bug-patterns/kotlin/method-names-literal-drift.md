# Hai literal hand-maintained drift mà không test nào bắt

## Triệu chứng
`SystemPropertiesSpoofModule.METHOD_NAMES` và
`AntiDetectScanModule.PROP_METHOD_NAMES`: 2 literal 9 tên method độc lập,
0 sync test. Một bên thêm tên mà bên kia quên → hoặc là overload không
được spoof, hoặc là call không được trace — drift câm.

## Root cause
2 bản copy hand-maintained ở 2 module khác nhau, không có check build-time
nào enforce invariant "hai set phải giống hệt nhau".

## Fix
`MethodNamesSyncTest` (JUnit4, `lsmodule/src/test/.../sync/`): parse cả 2
literal từ source bằng file-IO + regex (không load class — 2 module import
`android.*`, không load được trên host JVM), assert set equality, message
lỗi liệt kê cả 2 chiều thiếu. Theo convention `ProfileToggleSyncTest`
(`FeatureListSyncTest.moduleFile()`).

## Check chạy được
- `:lsmodule:test` xanh (cả 2 literal đang là 9 tên giống hệt).
- Kiểm chứng âm: sửa 1 tên trong 1 set → test đỏ, message chỉ rõ chiều thiếu.
- Phòng: mỗi khi tạo cặp literal song sinh ở 2 nơi → viết sync test ngay
  trong cùng commit; parse từ source thay vì import class khi module có
  dependency Android.
