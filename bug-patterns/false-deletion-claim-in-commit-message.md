# Bug pattern: commit message claim xóa file nhưng diff không có deletion

## Triệu chứng
Commit message ghi "Delete from tree: keystore.properties, ..." nhưng sau
commit, `git ls-tree -r HEAD --name-only` vẫn liệt kê đủ 3 file;
`git show --stat <sha>` không có dòng deletion nào;
`git log --diff-filter=D -- <path>` trống. Reviewer 2 pass verdict "correct"
mà không phát hiện. (Chiến dịch spoofx-security-fix, Wave 2, commit c6b789d,
2026-10-07.)

## Root cause
- Writer/coordinator tin lời nhau: message viết theo ý định, không theo diff thật.
- Reviewer soi diff để tìm defect trong code mới, nhưng không verify
  **negative claim** (cái được claim là "không còn tồn tại").
- Fable-check chạy không đủ sâu: claim "delete from tree" không được map tới
  evidence (`--diff-filter=D`).

## Fix
- `git rm --cached <files>` (giữ bản local, chỉ gỡ khỏi tree) + commit riêng
  với message trung thực, nêu rõ đây là phần Wave 2 làm thiếu.
- Verify sau fix:
  `git ls-tree -r HEAD --name-only | grep -E 'keystore.properties$|key.jks$|activation.properties$'`
  → trống; `git log --oneline --diff-filter=D -- <files>` → có entry.

## Check phòng (chạy được, cho vào fable-check mọi campaign)
Với mọi claim "xóa/xóa khỏi tree" trong commit message hoặc result file:
```bash
git diff --name-status <base>...HEAD | grep '^D'   # phải liệt kê đúng file
git ls-tree -r HEAD --name-only | grep '<pattern>' # phải trống
```
Không có dòng `D` tương ứng = claim sai, block commit.
