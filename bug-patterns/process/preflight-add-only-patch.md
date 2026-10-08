# Edit-script "chỉ thêm, không xóa" → trùng khai báo, không compile

## Triệu chứng
`preflight-edit check` PASS nhưng sau `apply`, file có 2 bản của cùng một hàm/KDoc
(`loadFromDir` ×2, `readOneFile` ×2 cùng JVM signature, KDoc tự mâu thuẫn) →
CI đỏ ở `compileKotlin`/`compileTestKotlin`. Lỗi lặp lại ở cả file main lẫn file test.

## Root cause
Edit-script của writer **không có một dòng `-` nào**: code cũ được dùng làm anchor
context, code mới toàn dòng `+`. `preflight-edit check` chỉ validate anchor tồn tại
+ unique — nó KHÔNG phát hiện "hunk này định thay thế nhưng không xóa bản cũ".
`apply` chèn sau anchor, giữ nguyên code cũ → duplicate declarations, double-catch,
statements mồ côi.

## Fix
- Mọi hunk thay thế code cũ BẮT BUỘC có dòng `-` xóa đúng những dòng cũ.
- Sau apply, coordinator grep verify: mỗi `fun`/`val` bị chạm phải đúng 1 hit;
  tokenizer kiểm tra brace/parens cân bằng (stripper regex thô dễ báo sai).
- KDoc: grep câu cũ phải 0 hit (chống "thêm mới mà quên xóa cũ" gây tự mâu thuẫn).
- Số dòng trong fingerprint phải đo lại BẰNG GREP sau apply, không đếm tay
  (pass 2 đo `:567`, patch chèn +10 dòng KDoc đẩy thành `:577`).

## Check phòng
- Reviewer checklist bổ sung: "patch có hunk nào toàn `+` mà không có `-` tương ứng không?
  Nếu có — hỏi writer đó là code mới hoàn toàn hay quên xóa cũ."
- Coordinator verify sau apply phải cover cả file test, không chỉ file main
  (P3-A: cùng failure mode lọt ở `HookErrorDiskStoreTest.kt` vì chỉ grep file main).

## Nguồn
SpoofX `spoofx-accurate-logging` P3-A, 2026-10-06. 3 pass writer mới xong
(P0 reviewer pass 1 → fix sai → revert → viết lại đúng).
