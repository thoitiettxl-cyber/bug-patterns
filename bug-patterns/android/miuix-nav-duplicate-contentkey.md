# miuix-nav throw "Duplicate contentKey" khi push trùng + coroutine activation kẹt `busy`

- **Triệu chứng:** hai đường crash toàn bộ thao tác UI, đều 100% repro
  thủ công, CI không bao giờ bắt vì CI không launch app:
  1. Tap nhanh 2 lần vào một nút điều hướng (hoặc 2 nút push cùng route)
     → miuix-nav throw `IllegalStateException: Duplicate contentKey` ngay
     trong `push`, app crash. (SpoofX, 2026-10-01, miuix-nav 0.9.4-rc01.)
  2. Nhấn "Kích hoạt"/"Làm mới" khi mất mạng hoặc worker timeout →
     `ActivationClient.activate/check` throw bên trong `scope.launch`;
     `busy` không bao giờ reset về `false` (dòng `busy = false` nằm SAU
     call có thể throw, không có `finally`), toàn bộ nút kích hoạt/làm mới
     bị disable vĩnh viễn; exception văng ra khỏi coroutine con → lan lên
     scope của composition → crash/lag UI.
- **Root cause:**
  1. `Navigator.push` forward thẳng `backStack.add(key)` mà không dedup.
     `backStack` là `MutableList` thường nên add trùng không lỗi ở phía
     mình — lỗi nổ ở miuix-nav khi nó sync stack vào `NavHost`, lúc đó đã
     muộn, không còn chỗ catch. Guard phải đặt ở ĐÚNG điểm này vì đây là
     choke point duy nhất: mọi màn hình đều push qua
     `LocalNavigator.push` (LocationScreen, MainScreen, ProfilesScreen).
     `SpoofXRoute` là `data object`/`data class` nên `==` so sánh theo
     structural equality — bắt được cả trường hợp 2 instance khác nhau
     nhưng cùng content.
  2. Mẫu `busy = true; scope.launch { ...throwable call...; busy = false }`
     là antipattern: bất kỳ exception nào giữa chừng cũng bỏ qua dòng reset.
     Trong coroutine, exception không được catch còn propagate lên parent
     Job (ở đây là scope bound vào composition) → hậu quả lan rộng hơn cả
     `busy` kẹt. Sửa đúng là `try { ... } catch { toast lỗi } finally {
     busy = false }` — reset là bất biến, toast lỗi tái dùng string đã có.
- **Fix:**
  1. Trong `Navigator.push`, thêm đúng 1 dòng guard trước `add`:
     `if (backStack.lastOrNull() == key) return`. Không cần try/catch
     quanh push — chặn trùng ngay từ đầu rẻ và chắc hơn bắt
     `IllegalStateException` của lib.
  2. Trong `runActivation()` và `runRefresh()` (SettingsScreen.kt): bọc
     toàn bộ body của `scope.launch` trong `try/catch (_: Exception)/
     finally { busy = false }`. Nhánh catch toast
     `R.string.settings_activation_network_error` — đúng string nhánh
     `NETWORK_ERROR` của `messageForCode` đã dùng, không thêm strings.xml.
     Giữ nguyên mọi logic khác: guard `NO_KEY` ở đầu `runRefresh`, nhánh
     toast có điều kiện `if (!resp.ok || ...)` không đổi.
- **Phòng (check chạy được — đã chạy thật 2026-10-01):**
  ```bash
  # mọi push qua Navigator đều đi qua guard dedup
  grep -n "lastOrNull() == key" \
    lsmodule/src/main/java/com/thoittxl/spoofx/ui/navigation/Navigator.kt # phải có hit
  # repo-wide: mỗi "busy = true" phải có 1 "finally" reset tương ứng
  f=lsmodule/src/main/java/com/thoittxl/spoofx/ui/screen/main/SettingsScreen.kt
  echo "busy=true: $(grep -c 'busy = true' $f) / finally: $(grep -c 'finally' $f)" # phải bằng nhau
  # catch trong 2 hàm activation phải toast string đã tồn tại, không string mới
  grep -n "settings_activation_network_error" \
    lsmodule/src/main/java/com/thoittxl/spoofx/ui/screen/main/SettingsScreen.kt # hit trong cả 2 catch
  ```
  Kết quả chạy thật sau fix: guard có hit ở dòng 15; `busy=true: 2 /
  finally: 2`; catch toast có hit ở cả 2 hàm (dòng 179, 207).
  Quy tắc: mọi `busy = true` đi kèm `scope.launch` PHẢI có `finally {
  busy = false }` trong cùng launch body; mọi wrapper quanh thư viện nav
  PHẢI dedup trước khi forward, vì lib throw ở tầng sync muộn hơn.
