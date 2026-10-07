# Cùng tên prefs ≠ cùng store: getSharedPreferences vs getRemotePreferences

Triệu chứng: toggle deep-gate `detach_apps` bật trong UI (Settings → "Công tắc hook"
→ "Cổng hook can thiệp sâu") nhưng plan luôn `1 install, 29 skip` — `detach_apps`
bị skip với `DEEP_GATE_OFF` vĩnh viễn, bất kể UI hiển thị gì. Không crash, không
log lỗi (skip reason chỉ ở `Log.v`, bị R8 strip ở release) — fail thầm lặng.

Case thật (2026-10-06, SpoofX v19.8, campaign `spoofx-deepgate-store-fix`):
`HookDebugSwitches.setDeepGate()` ghi `deep_gate_hook_keys={"detach_apps"}` qua
`appCtx.getSharedPreferences("profiles")` → file
`/data/data/com.thoittxl.spoofx/shared_prefs/profiles.xml` (dump thực tế 625B:
có gate key, KHÔNG có `_config`). Nhưng module trong target process đọc qua
`XposedModule.getRemotePreferences("profiles")` → libxposed `RemotePreferences`
→ binder IPC tới Xposed framework daemon → SQLite
`/data/adb/lspd/config/modules_config.db`. Hai store cùng chuỗi `"profiles"`
nhưng backend khác nhau, không có code nào sync. Module luôn thấy gate rỗng.

Root cause: nhầm "cùng tên" thành "cùng store". Comment trong code
(`PREFS_FILE` "must stay in sync" với `PREFS_NAME`) củng cố niềm tin sai —
đồng tên qua hai API khác nhau trỏ tới hai backend khác nhau. Kiến thức đúng
đã có trong codebase (`ProfileRepository` dual-write `_config` qua
`XposedService.getRemotePreferences`) nhưng feature mới (hma-essence B3) không
theo pattern đó, và reviewer không bắt vì tên trùng nhau.

Fix: mọi prefs module đọc PHẢI ghi qua `XposedService.getRemotePreferences`
(đường `ProfileRepository` dual-write). Cụ thể: `HookDebugSwitches.remotePrefsOrNull()`
(mirror `ProfileRepository.remotePrefsOrNull()`), dialog dùng remote khi service
bound, fallback local + dirty flag + reconcile khi bind (consume-after-push để
không resurrect key user đã gỡ).

Evidence verify (source API 102 local
`.agents/skills/libxposed-modern-api/docs/`, upstream GitHub bị ban):
- `XposedInterface.getRemotePreferences` javadoc: "Gets remote preferences
  **stored in Xposed framework**. Note that those are **read-only in hooked apps**."
- `XposedService.getRemotePreferences`: "Get remote preferences **from Xposed
  framework**." → `RemotePreferences.newInstance` → binder
  `requestRemotePreferences(group)`; write → `updateRemotePreferences`.
- Thực tế trên máy: `profiles.xml` có gate nhưng module skip `DEEP_GATE_OFF`;
  sau fix, plan hiện `install detach_apps`.

Phòng:
- Linkage check CI (`scripts/checks/prefs-store-linkage.sh`): cấm
  `getSharedPreferences("profiles")` ngoài allowlist (reconcile read +
  offline-fallback write). Escape hatch: `// ALLOW_DIRECT_PROFILES: <reason>`.
- Nguyên tắc: thêm prefs key mới mà module đọc → grep xem module đọc qua
  đường nào TRƯỚC khi chọn đường ghi; cùng tên string không phải bằng chứng
  cùng store.
- Test trên máy thật: bật gate → force-stop target → mở lại → plan phải hiện
  `install <key>` (không chỉ nhìn UI).
