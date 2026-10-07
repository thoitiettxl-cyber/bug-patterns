# Dead doc references deleted code

Triệu chứng: docs (ARCHITECTURE.md, skill SKILL.md) mô tả class/hàm như còn
tồn tại, kèm sample code, trong khi code đã bị xóa. Agent đọc doc sẽ viết
code không compile được (vụ SpoofX 2026-10-04: `arch/IHook.kt` bị xóa vì 0
subclass, nhưng 3 file doc vẫn mô tả nó như component hiện tại, gồm cả
sample `WifiSurface : IHook()` + `subHook(...)`).

Root cause: grep verify "0 caller" chỉ chạy trên `*.kt`, bỏ sót `.md`.
Xóa code mà không xóa doc = để lại "ảo giác hoàn chỉnh" ở tầng tài liệu.

Fix: sau khi xóa symbol, grep toàn repo KHÔNG giới hạn extension:
`grep -rn "SymbolName" . --exclude-dir=.git` (bao gồm .md, .kts, skills/).
Reviewer fresh-eyes bắt được vụ này ở pass 1 (writer sót), fix ở pass 2.

Check phòng chạy được:
```
grep -rn "IHook\|FingerprintMissException\|decodeInvoke\|decodeConstString\|decodeConstHigh16" \
  . --exclude-dir=.git --exclude-dir=build | grep -v "removed in the .* audit"
```
(kỳ vọng: chỉ còn historical note có chủ ý, hoặc 0 hit)
