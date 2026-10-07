# Verify artifact bằng máy, đừng kết luận bằng mắt

- **Triệu chứng:** tải artifact CI về, nhìn thấy 79 entry → tưởng file hỏng;
  thực ra là APK nguyên vẹn bị giải nén. (E-Muse, 2026-09-30.)
- **Root cause:** không hiểu cơ chế artifact của GitHub Actions:
  - Workflow `upload-artifact` với `archive: false` → endpoint
    `actions/artifacts/{id}/zip` trả về **raw file** (không bọc zip). APK bản
    thân là ZIP nên nhìn thấy entry APK là bình thường.
  - `gh run download` thì **giải nén** artifact thành các entry rời.
- **Fix — cách lấy APK đúng:** tải endpoint API zip vào 1 file, đặt đuôi
  `.apk`, rồi verify:
  ```bash
  unzip -l E-Muse-release.apk | head -3            # integrity
  unzip -p E-Muse-release.apk META-INF/version-control-info.textproto | grep revision  # đúng commit
  # có "APK Sig Block 42" khi quét binary
  ```
  Chỉ giao file cho Boss sau khi revision khớp commit CI.
- **Phòng:** mọi artifact giao tay đều phải có 2 bước: (1) lấy đúng cách,
  (2) verify bằng máy (revision + chữ ký). Không bao giờ giao file "nhìn có
  vẻ ổn".
- **Nguồn:** E-Muse 2026-09-30; `~/MEMORY.md` "Bài học artifact GitHub".
