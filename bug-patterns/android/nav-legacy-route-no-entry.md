# Legacy nav discriminator decode được nhưng không có entry → restore rơi vào chỗ không tồn tại

- **Triệu chứng:** sau khi nâng cấp app đổi cấu trúc navigation, process-death
  restore (hoặc mở app với saved back stack cũ) decode thành công route
  `Profiles`/`Apps`/`Settings` nhưng `NavDisplay` không có `entry<>` cho
  chúng → màn hình trống / crash. KDoc lúc đó còn claim "unknown
  discriminators fall back to Main" — sai: legacy discriminators là *known*
  (SerialName vẫn tồn tại) nên decode thành route thật, chỉ có unknown mới
  rớt về Main. (SpoofX, 2026-10-02: `NavBackStackSaver.decodeBackStack`.)
- **Root cause:** giữ deprecated route subclass cho backward-compat decode
  nhưng xóa nav entry của chúng ở MainActivity — decode OK ≠ navigable.
  KDoc mô tả behavior của unknown discriminator, không phải của legacy.
- **Fix:** trong `decodeBackStack`, map legacy routes → `SpoofXRoute.Main`
  sau decode (saved stack cũ vẫn restore được, về màn hình chính an toàn);
  sửa KDoc cho khớp; test `legacyRoutesDecodeToMain` pin behavior, cập nhật
  assertion trong `roundTripPreservesEveryRouteType` /
  `encodeDropsForeignKeysInsteadOfCrashingSave`.
- **Phòng (check chạy được):** khi thêm/xóa `entry<SpoofXRoute.X>` ở
  MainActivity, grep mọi subclass của sealed route — subclass nào không còn
  entry thì `decodeBackStack` phải map về route còn entry; test round-trip
  phải cover cả legacy discriminators cũ.
