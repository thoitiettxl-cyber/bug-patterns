# CI tìm artifact sai path so với plugin output

- **Triệu chứng:** CI build xong nhưng bước "locate artifact" fail
  "module zip not found", dù plugin đã sinh zip thành công.
  (tami-stealth, 2026-10-04 — phát hiện khi research HMA-OSS, chưa từng lộ
  vì build luôn fail sớm ở bước compile.)
- **Root cause:** ZygoteLoader Gradle plugin xuất zip vào
  `build/outputs/magisk/<flavor>/<buildType>/` (không flavor →
  `magisk/release/`, archiveName + `-<variant>` khi
  `isAddVariantToArchiveName=true`), nhưng step CI glob ở
  `magisk/*.zip` (thiếu 1 cấp `release/`).
- **Fix:** sửa glob CI thành `zygote/build/outputs/magisk/release/*.zip`,
  kèm comment ghi rõ quy ước path của plugin.
- **Phòng (check chạy được):**
  - Mọi step "locate artifact" trong CI phải được verify bằng 1 run xanh
    end-to-end, không chỉ "nhìn path có vẻ đúng".
  - Khi dùng Gradle plugin lạ, đọc source plugin (task `zipMagisk` /
    `getDestinationDirectory`) để lấy output path chính xác, đừng đoán.
- **Nguồn:** tami-stealth `nightly.yml`, ZygoteLoader
  `ZygoteLoaderDecorator.java` (pin `2a2160f`).
