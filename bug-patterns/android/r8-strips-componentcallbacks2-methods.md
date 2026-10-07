# R8 full mode strip method của `ComponentCallbacks2` → `AbstractMethodError` khi app background

- **Triệu chứng:** app crash khi bấm Nhập/Xuất hồ sơ (mở system file picker
  → app background → framework dispatch `onTrimMemory`):
  `java.lang.AbstractMethodError: abstract method "void
  android.content.ComponentCallbacks2.onTrimMemory(int)" on receiver
  java.lang.Class<c7>`. (SpoofX, 2026-10-02, logcat của Boss.)
- **Root cause:** 2 class của Compose UI (`AndroidComposeView` và callback
  nội bộ, obfuscated thành `ms`/`c7` trong release dex) implement
  `ComponentCallbacks2` nhưng R8 full mode + flags aggressive
  (`-repackageclasses ''`, `-allowaccessmodification`) đã strip SẠCH các
  method interface (`onTrimMemory`/`onLowMemory`/`onConfigurationChanged`).
  Verify bằng dexdump trên release APK: class `Lc7;` có
  `Interfaces: ComponentCallbacks2` nhưng `Direct methods: -`,
  `Virtual methods: -` — rỗng hoàn toàn. Không phải lỗi library (AAR gốc
  compile được nên input có method), cũng không phải code app (source không
  có reference nào tới ComponentCallbacks).
  Vì SAF picker (import/export) luôn đẩy app xuống background → framework
  gọi `onTrimMemory` → crash. Bất kỳ flow nào background app cũng có thể
  trigger.
- **Fix:** force-keep method interface trên MỌI implementer, thêm vào
  `lsmodule/proguard-rules.pro`:
  ```proguard
  -keepclassmembers class * implements android.content.ComponentCallbacks2 {
      public void onConfigurationChanged(android.content.res.Configuration);
      public void onLowMemory();
      public void onTrimMemory(int);
  }
  ```
- **Phòng (check chạy được):**
  ```bash
  # sau khi CI build xong APK release, verify trực tiếp trên dex:
  unzip -p app.apk classes.dex > /tmp/check.dex
  dexdump -d /tmp/check.dex | grep -A12 "Class descriptor  : 'Lc7;'" 
  # phải thấy onTrimMemory/onLowMemory/onConfigurationChanged trong Virtual methods
  #
  # audit định kỳ: liệt kê mọi class implement framework-callback interface
  # mà rỗng method:
  dexdump -d classes.dex | awk '/Class descriptor/{c=$3} /Direct methods *-$/{d=1} /Virtual methods *-$/{if(d) print c; d=0} /Virtual methods/{d=0}'
  ```
  Luật: **với R8 full mode + aggressive flags, mọi method mà framework gọi
  qua interface (không thấy call site trong app code) đều phải có keep rule
  tường minh** — R8 không tự biết framework sẽ gọi chúng.
- **Blast radius (xác nhận từ Boss 2026-10-02 ~16:00 sau khi cài bản fix):**
  MỘT root cause này giải thích 3 triệu chứng tưởng riêng biệt:
  1. Nhập/Xuất "không hoạt động" — mở SAF picker → background → crash.
  2. Chọn ngôn ngữ bị "out ra màn" — LocaleManager recreate/kill UI →
     `TRIM_MEMORY_UI_HIDDEN` → crash → văng ra launcher.
  3. Chuyển app qua lại "bị về Home" — background → crash → process chết
     → mở lại là cold start về tab Home mặc định.
  Hệ quả: fix `singleTask` (mục "nhảy Home") và LocaleManager trước đây chỉ
  chữa triệu chứng/nguyên nhân phụ; crash mới là gốc. `TRIM_MEMORY_UI_HIDDEN`
  fire MỌI lần app background nên app chưa từng sống sót dưới background.
- **Nguồn:** SpoofX `lsmodule/proguard-rules.pro`, release APK
  `spoofx-nightly-liquid.apk` (dexdump), logcat Boss 2026-10-02 15:36.
