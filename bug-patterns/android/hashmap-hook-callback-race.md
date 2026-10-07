# HashMap dùng trong hook callback đa thread → race / vòng lặp vô hạn

- **Triệu chứng:** Crash khó tái hiện (`ConcurrentModificationException`,
  ANR, hoặc `HashMap.get` treo do resize race) chỉ xảy ra trong target app
  bị hook — không bao giờ tái hiện trên máy dev. (SpoofX, 2026-10-02:
  `arch/ReflectUtil.kt` — `fieldCache`/`methodCache`.)
- **Root cause:** `HashMap` không thread-safe; cache reflection bị đọc/ghi
  từ hook callbacks chạy trên nhiều binder threads khác nhau của process
  target. Dạng put-if-absent thủ công (`cache[key]?.let { return }` rồi
  `cache[key] = v`) còn cho phép 2 thread cùng tính toán và ghi đè nhau.
- **Fix:** đổi sang `ConcurrentHashMap` (`java.util.concurrent`); mọi
  get/put qua toán tử `[]` vẫn compile y hệt. Values coi như immutable sau
  khi insert nên không cần đồng bộ thêm.
- **Phòng (check chạy được):**
  `rg --type kotlin "private val \w+[Cc]ache = HashMap" lsmodule/src/main/java`
  phải rỗng; cache nào trong `hooks/`/`arch/` được chạm từ callback đều phải
  là `ConcurrentHashMap` (hoặc bọc `synchronized`).
