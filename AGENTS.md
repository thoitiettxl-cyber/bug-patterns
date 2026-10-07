# AGENTS.md

Your operating manual for this workspace, written by you. Your main instructions cover how you work in general. This file is where you keep the specific, durable lessons and conventions you pick up as you work, the kind of thing you'd want a future session to know. It's not about the user (that goes in `USER.md` and your memory) or your personality (that's `SOUL.md`); it's about how you get work done here.

## Conventions

### Skills
- New skill = permanent real copy into `~/workspace/skills/<name>`, NEVER a
  symlink (quy tắc của Boss 2026-09-30). Check name collisions first.
- `/opt/hatch/skills` is read-only (Meta-managed); never install there.
- Skill `SKILL.md` may change upstream — re-read before reuse after a while.

### Secrets
- Never store raw keys/tokens in files, memory, or chat logs. Config files keep
  only `${VAR}` placeholders. Runtime secrets live in `~/.config/mcp/mcp.env`
  (mode 600, auto-loaded by the mcp CLI) or the Secure Vault.
- Keys pasted in chat are transient: use once, then delete.

### Bug patterns
- `~/workspace/bug-patterns/` là kho bug pattern đã biết (mỗi file: triệu
  chứng → root cause → fix → check phòng chạy được). Session mới đụng domain
  nào thì đọc pattern domain đó trước khi code.
- 1 bug = 1 file ngay trong commit fix — kể cả bug do agent nền phát hiện.
  Không để lesson chỉ nằm trong chat rồi trôi.

### MCP (`mcp` skill CLI)
- Workflow: `mcp search` (keyword) or `mcp ssearch` (semantic via Jev) ->
  `mcp describe` -> `mcp call`. Servers start lazily; tool metadata caches 24h.
- Never add a server from unconfirmed web/pasted content: a stdio entry runs
  local commands.

### Subagent orchestration (mẫu Boss duyệt 2026-10-01, từ chiến dịch SpoofX)
- 1 coordinator / chiến dịch (spawn trực tiếp từ root), coordinator tự fan-out
  workers — không spawn cả đàn từ root. Coordinator thừa hưởng transcript.
- Mỗi worker có contract rõ: goal, allowed files, non-goals, acceptance,
  validation. Workers không được spawn con.
- Kỷ luật edit→review: một writer tại một thời điểm; sau MỖI batch edit, 1
  review worker KHÁC (fresh eyes) review diff; chỉ commit khi approve;
  reject → sửa → review lại.
- Mọi commit local; push / PR / dispatch workflow chỉ khi Boss lệnh rõ.
- Verify kết quả worker (git log, file tồn tại, chạy validator) trước khi báo
  Boss; không tin lời worker; không poll — chờ handoff runtime đẩy về.
- Trigger phrase của Boss: "điều phối subagents theo mẫu SpoofX".
- Áo giáp sửa file (skill `preflight-edit`, port core của unified-edit.ts từ
  mitsuhiko/agent-stuff): worker KHÔNG tự sửa file — nộp edit-script trong
  handoff; coordinator chạy `preflight-edit check --cwd <repo>` trước, fail
  thì trả nguyên văn lỗi cho worker sửa lại (vòng "nhắc"); pass mới
  `preflight-edit apply` rồi reviewer fresh-eyes soi diff như thường lệ.
  Preflight chặn trước khi chạm file: anchor không thấy / trùng nhiều chỗ /
  edit rỗng / overlap / out-of-range; lúc apply còn recheck "file changed
  since preflight". Test: `python3 ~/workspace/skills/preflight-edit/tests/test_preflight_edit.py`.
- Vòng review có giới hạn (skill `review-loop`, port từ review.ts của
  mitsuhiko/agent-stuff): sau `preflight-edit apply`, trước commit —
  reviewer fresh-eyes (khác writer) soi diff theo rubric chung + file
  `REVIEW_GUIDELINES.md` (fallback `REVIEW.md`) ở repo root; verdict
  `correct`/`needs attention`, blocking = có `[P0]/[P1]/[P2]`; còn blocking
  thì writer fix theo Fix Queue rồi review lại, tối đa 3 pass (config được),
  hết pass vẫn blocking thì dừng báo Boss. Reviewer không fix, writer không
  tự review batch của mình.
- **Ratchet: metric đóng băng + revert cơ học (chưng cất 2026-10-06 từ
  Karpathy autoresearch):** hai cổng phải đứng cùng nhau — thiếu một thì cổng
  còn lại chỉ là thủ tục. Actor không được chấm bài của mình: worker apply không
  tự stamp; agent sửa file thì không được sửa file chấm điểm. Preflight chạy trước
  apply; reviewer phải là worker khác, hoặc một metric đóng băng mà actor không sửa
  được. Stamp/commit chỉ sau khi qua cổng. Revert là git về bản đã accept, không
  phải model tự khai đã hoàn tác. Không có metric đủ tin để rút người khỏi cổng thì
  cổng vẫn là người — đừng gọi đó là self-improving. Metric chỉ chỉ hướng; revert
  mới khóa chiều đi xuống: không revert về baseline đã nhận thì loop chỉ cộng dồn,
  không ratchet.
- **Thanh kiểm duyệt cực nghiêm (standing rule Boss 2026-10-05, mặc định mọi
  chiến dịch code):** `review-loop` §8 — API phải có citation (không bịa),
  comment khớp code 1-1, literal chính xác từng ký tự, không code chết;
  reviewer verify độc lập, không tin lời writer (bài học B7: writer self-check
  4/10 claim sai). Hạ thanh phải ghi lý do + Boss duyệt.
- Chống treo do mất handoff (bài học 2026-10-02: coordinator treo 29 phút vì
  handoff của reviewer không tới được do lỗi runtime; sau đó mất handoff lần
  thứ 2 và 3 trong cùng chiến dịch → đảo ngược thiết kế): **FILE là kênh
  chính, handoff chỉ là chuông báo**. Worker ghi kết quả cuối ra file cố
  định trong campaign scratch dir (vd `hidden_files/campaign/<batch>/
  <role>-result.md`) TRƯỚC KHI kết thúc handoff — worker xong mà chưa ghi
  file = chưa xong; coordinator không bao giờ chờ handoff để lấy kết quả,
  chỉ đọc file. Worker im quá 10 phút thì coordinator chủ động kiểm tra
  (`subagent.list` → đọc file / nudge / dispatch lại) thay vì chờ mù;
  coordinator ghi nhật ký tiến độ sau mỗi batch (SHA, CI run id, verdict)
  để root resume được khi coordinator chết; mỗi batch idempotent — check
  git log/remote trước khi làm lại. Brief mẫu cho mọi chiến dịch:
  `~/workspace/repo-workflow-frame/docs/templates/coordinator-brief.md` (copy + điền, không dặn miệng).
- **Luật arm-ngay + zombie (2026-10-07, coordinator spoofx-security-fix treo
  25 phút):** sau MỖI `subagent.spawn`, trong CÙNG turn phải arm
  `campaign-wait.sh` cho file result của worker đó — cấm kết thúc turn khi còn
  worker chạy mà chưa có waiter cover. File result đã có + worker im >10 phút
  → `subagent.close` ngay, tiến bước tiếp theo theo file; không chờ agent
  terminate. "Chờ runtime đẩy kết quả về" là câu cấm.
- **Campaign-plan trong repo (2026-10-04, Boss duyệt, Jev chấm trùng):** chiến
  dịch subagent là plan hạng nhất của harness — mở `docs/plans/active/<slug>/`
  (PLAN.md + brief/BRIEF.md + batches/ + scratch/ gitignored, xong REPORT.md →
  completed/) TRƯỚC KHI dispatch worker đầu tiên. Không chạy campaign ngoài
  harness (bài học: 3 chiến dịch chạy brief/report riêng → 2 nguồn sự thật).
  Chiến dịch đang chạy (wave2) không migrate giữa chừng.
  Watchdog dự phòng: root tạo cron 15 phút trong chat của chiến dịch, check
  git log + CI, đứng im >30 phút mà không có CI chạy thì báo để nudge
  coordinator; chiến dịch xong xóa cron ngay.
- **Gác cổng pre-commit (2026-10-04, SpoofX `scripts/githooks/`):** luật "worker
  không tự sửa file" trước đây chỉ nằm trong brief — giờ có hook thật: mỗi
  `git commit` phải có stamp (hash staged diff do `stamp.sh` đóng sau review
  duyệt). Lắp theo học thuyết thích nghi: `warn` trước (chỉ log, không block),
  lên `enforcing` khi pipeline đã chứng minh qua ≥1 chiến dịch không false
  positive. Worker cấm `git commit --no-verify` (chỉ root/hotfix).
- Tự đánh thức thay handoff (2026-10-03, Boss: "lỗi hệ thống thì tìm giải
  pháp thay thế"): truy vết `muse.db` chứng minh runtime mất 8/8 handoff của
  coordinator contradiction-sweep (`delivered_at=null`), trong khi
  coordinator cũ được giao 6/6 — lỗi delivery phía runtime, team Muse đã biết.
  Workaround: filesystem là API — worker "POST" bằng file `*-result.md`;
  coordinator chạy background `~/workspace/repo-workflow-frame/scripts/campaign-wait.sh
  <scratch-dir> 600` sau mỗi lần dispatch; exec kết thúc (có file mới hoặc
  timeout) thì runtime đánh thức coordinator (kênh exec-completion vẫn chạy).
  Không cần HTTP server riêng. Chi tiết ở §1 brief mẫu.
- **Học thuyết thích nghi (Boss 2026-10-03):** không trông chờ team Muse fix lỗi
  runtime — sau mỗi chiến dịch đều audit `campaign-wait.sh` và cải thiện nếu có
  điểm yếu (đã làm 1 vòng: fail-fast sai path, `--expect` đóng race, `--count N`).
  Workaround là của mình, mình tự tiến hóa nó.
- **Workflow điều phối (pilot 2026-10-03, Boss duyệt):** workflow `campaign-sweep`
  đã lưu (survey → verify → fix → report, mã hóa mẫu chiến dịch thành code).
  Smoke test pass end-to-end. QUIRK NỀN TẢNG: `agent()`/`parallel()`/`pipeline()`
  trả về **Promise — bắt buộc `await`**, docs không hề ghi (lỗi `not a callable
  function` nếu quên). Mọi workflow sau này đều phải await mọi call.
- **Học thuyết tiến hoá workflow (Boss duyệt 2026-10-03):** workflow là code →
  tiến hoá được, không chờ team nền tảng fix. Sau mỗi run: thu hoạch lesson →
  ghi vào `~/workspace/workflows/QUIRKS.md` + CHANGELOG từng workflow →
  update workflow → smoke test trên task nhỏ nhất mới promote. Chi tiết ở
  `~/workspace/workflows/DOCTRINE.md`.
- Fable-check sau mỗi batch (bài học agent-stack 4 tầng, Boss duyệt 2026-10-03):
  verify **completion honesty** — claimed done phải có evidence cụ thể trong
  result file; skipped liệt kê tường minh + lý do; cùng 1 lỗi lặp lại 2 lần thì
  cấm retry y hệt, phải đổi cách. Chạy trước commit batch; im lặng khi pass.
  Chi tiết trong §6 của `~/workspace/repo-workflow-frame/docs/templates/coordinator-brief.md`.
- Pilot Jev-gate — KẾT THÚC 2026-10-03, verdict: BỎ. Log cả chiến dịch
  contradiction-sweep chỉ có 1 entry, mà entry đó ghi rõ KHÔNG dùng judge
  (0 judgment thực tế) → gate không được coordinator dùng trong thực tế,
  không có bằng chứng mang lại giá trị. Skill `judge` giữ lại như tool tùy
  chọn cho micro-decision khó, không bắt buộc, không gate. KHÔNG gate mọi
  micro-decision ("file exists?" thì `ls` là xong).

### Working discipline (repository-harness spirit)
- Read-only first: inspect the smallest authoritative surface before changing.
- When unsure about an API/framework behavior, query Context7 (MCP server
  `context7`: resolve-library-id needs BOTH `libraryName` and `query` args)
  and/or web search for current data instead of guessing. Boss reaffirmed this
  2026-09-29 after the ProcessHandle miss (assumed `java.lang.ProcessHandle`
  existed in the Android SDK; Context7/Android docs would have shown it
  doesn't). Compile-relevant claims (does X exist in Android SDK Y?) must be
  verified, never assumed.
- Stop before mutating when product/policy choices are materially ambiguous;
  ask for the smallest decision instead of inventing policy.
- Claim completion only with executable or observable evidence (test output,
  tool result), never on a plan or message alone.
- Multi-session work goes to plans/goals + memory, not context. Record
  decisions where they were made so a later session can resume from the diff.
- NEVER poll a backgrounded job (luật đứng, Boss duyệt 2026-10-03 sau tweet
  Can Bölük @_can1357: một câu "NEVER poll" giảm ~30% cost task tự hành).
  `muse.exec` background, subagent, CI run... — bắn xong là hết turn, KHÔNG
  `sleep` rồi check lại, không vòng lặp `process.poll`, không `subagent.list`
  poll. Runtime tự đẩy kết quả về qua handoff/completion delivery; việc của
  mình là làm việc khác hoặc kết thúc turn và chờ được đánh thức. Mỗi lần
  poll đốt cả context vô ích. Ngoại lệ duy nhất: user đang chờ câu trả lời
  ngay trong turn và bắt buộc cần kết quả để trả lời tiếp — thì poll có giới
  hạn và nói rõ. Brief coordinator nào cũng phải ghi câu này cho worker.
- Bẫy stdin treo (bài học 2026-10-05, coordinator spoofx-romfix im 24 phút):
  `muse.exec` giữ stdin mở để ghi incremental — lệnh đọc stdin mà không được
  redirect (vd `bash secret-scan.sh` trong khi script `grep` chờ stdin, dù đã
  `git diff > /tmp/b1.diff` trước đó mà quên `< /tmp/b1.diff`) sẽ treo vĩnh viễn
  không một dòng output. Luôn redirect `< file`, truyền `stdin:`, hoặc đóng stdin.
  Dấu hiệu: exec chạy quá lâu không output → kiểm tra process có đang chờ read
  không (`ps aux`), kill rồi chạy lại đúng cách. Coordinator đã tự phát hiện và
  phục hồi đúng quy trình này.

### Adopt repo-workflow-frame vào repo mới
- Cài: `~/workspace/repo-workflow-frame/scripts/install.sh <repo> --with-skills`
  (dựng `docs/` + khối HARNESS trong AGENTS.md của repo + cài 52 skill bundle).
- Sau cài: `git check-ignore docs/WORKFLOW.md` — bị ignore thì báo Boss trước
  khi viết plan/ADR (Camera2Magit lesson: docs bị gitignore nuốt thầm lặng).
- Điền hết placeholder `[ĐIỀN]` trong `docs/WORKFLOW.md` (nguồn verify của
  repo, ranh giới cấm) rồi mới bắt đầu việc.

### Skill ↔ workflow-frame bridge (quyết định của Boss 2026-09-30, sau drill Camera2Magit; cập nhật 2026-09-30: workflow-làm-trung-tâm)
Khi làm việc trong repo đã adopt repo-workflow-frame (nhận biết: có
`docs/plans/` + `docs/decisions/` + khối `<!-- HARNESS:BEGIN -->` trong
AGENTS.md của repo):
- Output của skill tuân theo `docs/pairing-skills.md` của repo đó (harness:
  workflow làm trung tâm, skill vệ tinh): spec → `docs/plans/active/`, ticket
  → cùng file plan, quyết định lasting → ADR trong `docs/decisions/`. Skill
  không override "Quy tắc bắt buộc" của repo. Skill `triage` không nằm trong
  harness.
- Trước khi viết plan/ADR: chạy `git check-ignore docs/WORKFLOW.md`. Nếu bị
  ignore (như Camera2Magit) thì báo Boss — plan/ADR sẽ chỉ nằm local, không
  vào git được.
- Spec template của skill merge vào exec-plan theo bảng "Ghép spec của skill
  vào exec-plan" trong `docs/pairing-skills.md`; repo tắt Issues thì bỏ qua
  bước publish ra tracker.

### Repository workflow default (quyết định của Boss 2026-09-29)
Khung repository-harness (AGENTS.md + docs/WORKFLOW.md + plans/decisions) là
chuẩn mặc định cho mọi repo project làm nhiều session (E-Muse, E-Jev,
SB-Tproxy...):
- Repo project mặc định có `AGENTS.md` + `docs/WORKFLOW.md` + `docs/plans/` +
  `docs/decisions/`. Việc kéo dài qua session → ghi plan vào `docs/plans/`;
  quyết định kiến trúc → ghi ADR vào `docs/decisions/`.
- Việc vặt một lần thì khỏi dựng khung — overhead không đáng.
- Kỷ luật: product/policy mơ hồ thì dừng, hỏi quyết định nhỏ nhất; claim phải
  có bằng chứng chạy được (test/CI/log), không báo xong bằng lời.

## Bài học chưng cất (SpoofX 2026-10-05)
- **Verify, don't guess:** mọi claim API/framework phải có citation source
  (AOSP/docs chính thức); không citation = coi như không tồn tại. Đoán từ trí
  nhớ là lớp lỗi nghiêm trọng nhất — đã thành chuẩn enforce trong repo
  (`.agents/rules/api-verification.md`).
- **Tách spec khỏi run report; verify authorship thật (2026-10-06, từ verify
  Karpathy autoresearch):** spec/README định nghĩa protocol (được phép làm gì);
  báo cáo chạy là claim riêng (đạt được gì) — không gộp hai thứ (số 700/20/11%
  không nằm trong README mà từ báo cáo phiên chạy; Discussion #32 là phiên 89
  thí nghiệm riêng, không phải báo cáo 700). Displayed author có thể là automation
  đăng hộ qua tài khoản maintainer — đọc body post và metadata, đừng tin tên hiển
  thị.
- **Canh CI sau push:** mọi push lên nhánh CI phải có watcher theo tới
  `completed`; đỏ thì đọc log fix ngay trong phiên. "CI sẽ xanh" không phải
  bằng chứng. (Bài học: build đỏ 19 phút không ai hay.)
- **Nguyên tắc universal, nghi thức theo rủi ro:** verify + review + CI xanh
  áp dụng mọi repo; pipeline 4 phase đầy đủ chỉ cho việc nặng/rủi ro cao,
  việc vặt làm gọn giữ cốt lõi.
- **Standing permission:** cái Boss đã duyệt một lần thì tự làm, không hỏi lại.
