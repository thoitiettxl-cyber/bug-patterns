# preflight-edit: dòng context thiếu marker space → mất 1 space indent mỗi lần apply

## Triệu chứng
Sau `preflight-edit apply`, các dòng context trong hunk mất đúng 1 leading
space (8→7, 12→11, 4→3), trong khi dòng `+` mới giữ nguyên indent. Diff đầy
noise whitespace; `preflight-edit check` vẫn báo OK (fuzzy match cho pass
dù context không khớp exact).

## Root cause
1. **Worker viết sai format:** trong patch Codex/apply_patch, dòng context
   BẮT BUỘC bắt đầu bằng 1 space marker rồi mới đến nội dung
   (` context`, không phải `context` trần). Worker viết nội dung indent
   trực tiếp (không marker) → parser làm `raw[0], raw[1:]`, ăn ký tự space
   đầu của indent làm marker → body thiếu 1 space → apply ghi đè đúng
   bằng đó.
2. **Tool quá dễ dãi:** fuzzy whitespace matching cho pass dù context đã
   mất 1 space, rồi ghi đè file bằng bản sai — "check OK" không có nghĩa
   "không đổi gì ngoài ý định".
3. Coordinator cũng mắc khi sửa tay (dùng context line làm anchor mà nội
   dung anchor đã sai indent → fuzzy match rồi ghi đè sai).

## Fix
- Brief worker: dòng context = 1 space marker + nội dung (dòng code 8
  spaces phải viết 9 spaces đầu dòng). Không chắc → chỉ dùng cặp `-`/`+`,
  không dùng dòng context.
- Sau MỖI `apply`, chạy `git diff` và quét whitespace-only noise:
  script so từng cặp `-/+` trong hunk, stripped bằng nhau nhưng raw khác
  nhau → báo ngay.
- `@@` + text bị hiểu là context phải tìm trong file → dùng `@@` trần.

## Check chạy được
- `git diff <base> -- <files> | python3 wsdiff.py` → 0 dòng WS-ONLY.
- Phòng: cho vào template brief mọi campaign dùng preflight-edit; cân nhắc
  patch tool để `check` fail khi context chỉ khớp fuzzy (thay vì silently
  rewrite).
