# Flush reconcile lọc prefix cứng: họ toggle key mới kẹt local vĩnh viễn

Triệu chứng: toggle bật trong UI khi Xposed framework chưa bind → UI (đọc
local mirror) hiện ON, nhưng module trong target process (đọc remote prefs)
thấy OFF vĩnh viễn — dù reconcile đã chạy sau khi bind. Không crash, không
log, fail thầm lặng: user tưởng đã bật nhưng hành vi không đổi.

Case thật (2026-10-06, SpoofX, campaign `spoofx-compliance-fix` batch B1/P0):
`setSentinelResetEnabled` (ProfileRepository.kt) dual-write local + remote
khi bound; khi unbound chỉ ghi local + dirty flag. KDoc claim "the dirty flag
makes the reconciler push it on the next bind" — SAI: reconciler gọi
`pushToggleKeysToRemote`, nhưng hàm này whitelist cứng chỉ flush key
`startsWith("profile_enabled_")` (cả early-return lẫn loop). Key
`sentinel_reset_enabled_<pkg>` không bao giờ tới remote → UI và module lệch
nhau vĩnh viễn.

Root cause: hàm flush reconcile được viết cho 1 họ key (`profile_enabled_*`),
sau này thêm họ key thứ hai (`sentinel_reset_enabled_*`) mà không mở rộng
filter. Whitelist prefix cứng nằm ở 2 chỗ trong cùng 1 hàm (early-return +
loop) — cả 2 phải đổi cùng nhau. Reviewer không bắt vì KDoc của setter claim
sai nhưng trông đúng (dirty-flag → reconcile → push), và không ai đọc lại
body `pushToggleKeysToRemote` khi thêm toggle mới.

Fix: `pushToggleKeysToRemote` flush cả hai prefix — `PROFILE_ENABLED_PREFIX`
(`"profile_enabled_"`) và `SentinelIdentityManager.TOGGLE_PREFIX`
(`"sentinel_reset_enabled_"`, single source of truth) — qua helper
`isToggleKey()` dùng chung cho early-return và loop; cập nhật KDoc của
`pushToggleKeysToRemote`/`setSentinelResetEnabled` và comment ở commit path
cho khớp code 1-1. Cả 3 callers (commit path, reconcile LOCAL, reconcile
REMOTE) hưởng fix mà không đổi gì. Format key không đổi (module đọc
`TOGGLE_PREFIX + packageName` tại `SpoofXModule.kt:248`).

Evidence verify (đọc source trực tiếp, số dòng pre-fix):
- `pushToggleKeysToRemote` (ProfileRepository.kt:742-756): early-return `:743`
  và loop `:746` đều `startsWith(PROFILE_ENABLED_PREFIX)` — không nhánh
  sentinel nào.
- `ProfileStoreReconciler.choose`: `if (local.dirty) return LOCAL` → toggle
  bật lúc unbound chắc chắn vào nhánh LOCAL → `:808`
  `pushToggleKeysToRemote` — đường flush tồn tại, chỉ bị filter loại.
- `SentinelIdentityManager.TOGGLE_PREFIX = "sentinel_reset_enabled_"`
  (identity/SentinelIdentityManager.kt:41); `ProfileRepository` đã import
  class này (`:231`, `:238`, `:252`).

Phòng:
- Check chạy được — thêm họ toggle key mới (module đọc) thì chạy:
  `grep -rn 'startsWith(' lsmodule/src/main/java/com/thoittxl/spoofx/data/ProfileRepository.kt`
  và hỏi "hàm flush/sync nào lọc theo prefix?" — whitelist prefix cứng phải
  được review như API contract.
- Linkage check CI: prefix xuất hiện trong flush filter phải khớp danh sách
  toggle-prefix mà module đọc (quét usages của `TOGGLE_PREFIX` /
  `PROFILE_ENABLED_PREFIX`); escape hatch `// NO_FLUSH: <reason>`.
- Test trên máy thật: unbind framework → bật toggle → bind lại → đọc remote
  prefs trong target process phải thấy key (không chỉ nhìn UI).
