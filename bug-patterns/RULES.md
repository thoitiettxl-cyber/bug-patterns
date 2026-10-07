# Bug-patterns — quy tắc theo nhóm

> Mỗi rule: pattern chung + check phòng + số file nguồn.
> File đầy đủ: `~/workspace/bug-patterns/`. Quy tắc: 1 bug = 1 file ngay trong commit fix.

## 1. Nâng toolchain/SDK → verify lại mọi thứ từng đúng (4)
AGP 9 xóa task test, bundle Kotlin riêng, API mới compile qua nhưng `NoSuchMethodError` trên minSdk (cần desugaring), sdkmanager đổi tên package (`android-37.0`).
**Check:** nâng major → liệt kê task thật, đọc CI log compiler version, `sdkmanager --list`, review mọi API post-minSdk. Compile xanh ≠ chạy được trên minSdk.

## 2. Cấm đoán API/symbol — verify qua nguồn authoritative (5)
`getSpeedAccuracyMetersPerSecond` không tồn tại, copy file thiếu symbol đừng vội kết luận "library chưa release", bảng opcode copy bằng mắt sai 32 entry, `JUnit fail()` trả `Unit` không phải `Nothing`.
**Check:** claim API → Context7/AOSP source/`javap`/sources.jar; bảng port từ nguồn khác → script verify tự động; comment "verified" phải ghi kèm *cách* verify.
⚠️ File `android/miuix-unreleased-liquid-glass-api.md`: kết luận gốc SAI (đã đính chính 2026-10-02 — 4 symbol là file local bị copy thiếu); chỉ phần Phòng còn giá trị.

## 3. Hook stealth: cover MỌI overload/entry point, đúng kiểu trả về (5)
Detector lách qua overload `(int)` khi mình chỉ mask `(String)`; `getStringForUser`/`NameValueCache` lách `getString`; `param.result = null` trên method trả primitive → unbox NPE; `HashMap` cache trong callback multi-thread → race.
**Check:** liệt kê mọi overload cùng semantic; `param.result` không bao giờ `null` cho primitive; cache multi-thread dùng `ConcurrentHashMap`.

## 4. State Compose/VM: publish copy mới, không early-return qua post-commit (5)
Mutate cùng instance rồi gán lại → Compose skip recompose; field rename không refresh sau save → ghost entry; nhánh DEFERRED `return` sớm như failure → bỏ qua post-commit; `Saver.save` không guard trong khi `restore` có → crash xoay màn hình.
**Check:** setter publish `working` phải là copy mới; refresh field sau save; trước `return` trong nhánh status kiểm tra `committed`; guard đối xứng 2 chiều.

## 5. Giả định sai framework/nav contract (7)
`AppCompatDelegate` là no-op trên `ComponentActivity`; `viewModel()` trần crash trong nav entry bị bọc; `Navigator.push` trùng key → throw muộn; `launchMode="standard"` mất nav state khi tap launcher; 2 prefs key cũ/mới cùng điều khiển theme.
**Check:** gọi API AppCompat → activity phải là `AppCompatActivity` thật; wrapper nav dedup trước khi forward; thêm/xóa nav entry → rà soát mọi subclass của sealed route.

## 6. Compose/Miuix UI: contract khác kỳ vọng (7)
Poll trong `LaunchedEffect` không bound → chạy vô hạn; `delay()` không dời blocking I/O khỏi Main; `TabRow` one-way → vuốt chết (cần `HorizontalPager` + sync 2 chiều); `ScrollBehavior` không attach `nestedScroll`; Miuix `Scaffold` không offset content dưới top bar (cộng `calculateTopPadding()`); header cố định nhét vào `LazyColumn` → "dải trắng".
**Check:** grep theo invariant (while trong ui/ phải có bound; `nestedScroll` attach đúng 1 lần; `decorationBox` có nhánh vẽ hint).

## 7. Background/service/OEM thù địch (9 — lớn nhất)
OnePlus vuốt tắt kill cả process (`START_STICKY` bị drop) → `onTaskRemoved()` tự restart; process con mồ côi giữ port → kill lúc start; supervisor loop thiếu generation guard → 2 loop quản 1 process; Quick Tunnel fail → named tunnel là đường chính; cold start persist rỗng đè prefs → seed từ prefs trong `onCreate`; `TYPE_ACCESSIBILITY_OVERLAY` chỉ add từ context của service; Android 14+ MediaProjection chỉ trong FGS type `mediaProjection`; explicit Intent + receiver động → broadcast rơi (dùng implicit + `setPackage()`); binary Go không đọc system CA.
**Check:** mọi FGS phải có `onTaskRemoved`; mọi spawn phải có kill + cleanup lúc start.

## 8. R8 full mode + port từ binary: đừng "hợp lý hoá" (5)
R8 strip method interface `ComponentCallbacks2` → `AbstractMethodError` (1 root cause giải thích 3 triệu chứng SpoofX); port render loop từ disassembly: gán nghĩa field sai, "hợp lý hoá" điều kiện sai, 2 EGLConfig khác nhau (gốc dùng 1); `serializer<T>()` reified → reflective crash loop.
**Check:** port từ binary → tra ngược ai ghi field, map từng toán hạng, đối chiếu mọi nơi implement cùng công thức; R8 full mode → keep mọi method framework gọi qua interface.
📌 File `r8-strips-componentcallbacks2-methods` chỉ ra fix `singleTask` trước đây chỉ chữa triệu chứng của crash background.

## 9. Claim "xong" phải có evidence chạy được (7)
Merge không chạy CI trên nhánh feature → lỗi lọt; tải artifact CI sai cách → verify revision + chữ ký; CI tìm artifact sai path → verify bằng 1 run xanh end-to-end; feature 0 caller = chết; xóa symbol mà grep chỉ quét `*.kt` → doc còn mô tả class đã xóa; fix trim chỉ tầng ngoài → liệt kê TẤT CẢ `split(` trong hàm.
**Check:** branch feature → CI xanh trước merge; artifact giao tay → verify revision + chữ ký; xóa symbol → `grep -rn "X" . --exclude-dir=.git` (không giới hạn extension).
⚠️ `settings-source-url-404`: check "URL fetch 200" false positive với repo private → dùng `gh repo view` đã auth.

## 10. Quy tắc an toàn cứng (2)
Không bao giờ "tái tạo" secret từ trí nhớ — copy nguyên văn từ file gốc; config trong repo chỉ placeholder.
Checklist giao artifact bắt buộc: cold start giữ setting, reboot tự về, vuốt tắt hồi sinh, test đúng máy Boss, tắt tay không hồi sinh mù, không secret trong repo, verify artifact, CI xanh đúng commit. Thiếu mục nào → ghi rõ "chưa test X".

