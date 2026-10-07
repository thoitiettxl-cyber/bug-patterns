# RELEASE.md ghi sai artifact name + retention (D-P1-3)

- **Triệu chứng:** `RELEASE.md` ghi artifact `SpoofXManager*-release`, retention
  3 ngày — sai cả 2 so với workflow thật. (SpoofX, audit 2026-10-05.)
- **Root cause:** Docs viết trước khi workflow đổi sang `spoofx-release-apk` +
  retention 1 ngày.
- **Fix:** Theo `.github/workflows/android.yml` (block `upload-artifact`):
  name `spoofx-release-apk`, retention 1 ngày, chỉ bridge build→publish (APK
  release publish qua GitHub pre-release).
- **Check:** đọc block `upload-artifact` trong `android.yml` mỗi khi sửa
  `RELEASE.md` § release flow.
