# spoofx-toggle-without-ui-row — toggle implemented nhưng không có UI row

## Triệu chứng
- `ProfileToggle` mới với `implemented = true` nhưng không có row
  trong editor UI → user không thể bật/tắt nếu không sửa
  profile JSON tay.
- Batch 1 (commit `e8d1b7f`, campaign spoofx-toggle-ui-fix) ghi KDoc
  "JSON-only by design" cho `SPOOF_IME` / `HIDE_PROXY_PROPS` để hợp
  thức hoá việc thiếu UI — Boss REJECT: 2 toggle này PHẢI
  có UI vì user không biết JSON (campaign
  spoofx-toggle-ui-fix-2, 2026-10-06).

## Root cause
Không có check máy nào enforce "toggle implemented ⇒ có UI
row"; reviewer cũng không bắt được bug class này ở khâu
sản xuất (audit report
`docs/plans/active/spoofx-toggle-ui-audit/REPORT.md`). KDoc "JSON-only by
design" biến một thiếu sót thành quyết định có chủ ý, che mất bug.

## Fix
1. Wire UI row cho `SPOOF_IME` + `HIDE_PROXY_PROPS` vào
   `PRIVACY_SIMPLE_TOGGLES` (`PrivacyScreen.kt`) — đúng pattern batch 1
   (M-1/M-2). `SPOOF_IME` (category `IDENTITY_SPOOF`) vào cùng list vì
   PrivacyScreen không có section identity riêng, và list đã chứa
   sẵn `SPOOF_INSTALL_SOURCE_PLAY` / `SPOOF_BROWSER_FP` (cùng category).
2. Sửa KDoc bỏ note "JSON-only by design" (giờ đã có UI).
3. Script `scripts/checks/toggle-ui-linkage.sh`: với mỗi entry
   `implemented = true` → PASS nếu được reference trong `ui/`
   (row trực tiếp, `childrenOf(parent)`, hoặc category render generic
   qua filter `category == ToggleCategory.*` như DeviceScreen), hoặc KDoc
   có marker `NO_UI_ROW: <lý do>`; FAIL liệt kê offender, exit
   non-zero. Wire vào verdict-gate CI.
4. Mục 13 trong `REVIEW.md` (checklist review).

## Check (chạy được)
```sh
cd ~/workspace/SpoofX
bash scripts/checks/toggle-ui-linkage.sh
# kỳ vọng: PASS: 40 toggles have UI rows, 0 marked NO_UI_ROW, 0 offenders
# tự động bắt offender: thêm 1 toggle giả implemented=true
# không UI row → script FAIL liệt kê đúng tên đó, exit 1
# (lệnh mẫu với PROFILE_TOGGLE_FILE override: xem writer-result.md
#  của campaign spoofx-toggle-ui-fix-2)
```
