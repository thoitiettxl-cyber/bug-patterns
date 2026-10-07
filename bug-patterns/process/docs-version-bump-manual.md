# RELEASE.md "Version bump" lỗi thời (D-P1-4)

- **Triệu chứng:** `RELEASE.md` hướng dẫn bump tay `versionCode` mỗi release —
  đã lỗi thời từ khi nightly auto-increment. (SpoofX, audit 2026-10-05.)
- **Root cause:** `.agents/rules/release-rules.md` đổi scheme (`baseVersionCode`
  + CI `-PnightlyVersionCode`) nhưng `RELEASE.md` không theo.
- **Fix:** Section mới: scheme major×1000+minor×100, `baseVersionCode` là điểm
  bump duy nhất (versioned release), nightly auto `max+1` qua
  `-PnightlyVersionCode`, `bootstrap_nightly=true` lần đầu. Không hard-code số
  version cụ thể (tránh stale).
- **Check:** `RELEASE.md` § Version bump không mâu thuẫn `release-rules.md`.
