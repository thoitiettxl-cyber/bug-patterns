# AGP 9: task testReleaseUnitTest không tồn tại (chỉ debug có unit test)

- **Triệu chứng:** CI fail ở step test với
  `Cannot locate tasks that match ':lsmodule:testReleaseUnitTest' as task
  'testReleaseUnitTest' not found in project ':lsmodule'.`
  (Task-selection error, không phải compile error.) (SpoofX, 2026-10-01,
  AGP 9.3.2 + Gradle 9.7.1.)
- **Root cause:** AGP 9 chỉ tạo unit test component cho **debug variant** —
  task `testReleaseUnitTest` đã bị loại bỏ. Workflow cũ (viết cho AGP 8)
  vẫn gọi tên task này nên Gradle không resolve được. Tiền lệ public:
  soniqo/speech-android fix y hệt (2026-09-08).
- **Fix (SpoofX commit tương ứng):** workflow chạy `:lsmodule:test`
  (task tổng, chạy toàn bộ unit test hiện có — debug) thay vì
  `:lsmodule:testReleaseUnitTest`; sync lại validator
  (`scripts/validate-codex-harness.sh`) và doc/skills tham chiếu tên task
  cũ (AGENTS.md, docs/WORKFLOW.md, 3 skill doc) để gate không stale.
- **Phòng (check chạy được):**
  ```bash
  # sau mỗi lần nâng AGP major: liệt kê task test thật sự tồn tại
  # (chạy trên CI hoặc máy có Android SDK, không chạy trong sandbox)
  ./gradlew :lsmodule:tasks --all 2>/dev/null | grep -i "test.*UnitTest"
  # workflow/validator/doc không được hard-code tên task đã bị AGP xóa
  grep -rn "testReleaseUnitTest" .github/workflows/ AGENTS.md docs/WORKFLOW.md .agents/skills/ scripts/
  ```
  Luật: **nâng AGP major → verify lại tên task trong workflow bằng
  `tasks --all`, không tin tên task cũ.**
- **Nguồn:** SpoofX CI run `36843367210` (fail) → fix batch `:lsmodule:test`,
  2026-10-01.
