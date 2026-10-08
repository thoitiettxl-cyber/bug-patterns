# Cờ migration nằm trong payload mà nó định loại bỏ

**Ngày:** 2026-10-07 — SpoofX split-prefs follow-up (sau đo device: `prefs bundle = 321864 B`, `_config` chiếm 99,4%).

## Triệu chứng
Tách group prefs chạy được (`assign` 4,5KB + `profile_*` ~7KB), nhưng log target vẫn in `prefs bundle = 321864`. Code vẫn gọi `getRemotePreferences(<group cũ>)` rồi duyệt `.all` — mỗi target vẫn kéo 322KB qua binder, `Large reply` vẫn còn.

## Root cause
Cờ migration `split_prefs_migration` nằm TRONG group cũ (1 trong 22 key). Để đọc cờ quyết định "có bỏ group cũ không", code buộc phải pull cả group cũ trước — chicken-and-egg: cái cờ sinh ra để tránh pull 322KB lại chính là thứ bắt pull 322KB.

Cùng họ với lỗi "đo `prefs bundle` trong target": phép đo duyệt `.all` trên group cũ cũng là một pull 322KB trá hình.

## Fix
- Cờ cho target đọc (`split_done`) chuyển sang group nhỏ riêng `core` (<1KB): target pull `core` TRƯỚC, chỉ khi `split_done=true` mới bỏ qua group cũ. Cờ intent của manager (`split_prefs_migration`) giữ trong group cũ — target không bao giờ đọc nó.
- `split_done` chỉ được stamp SAU KHI `assign` + `profile_*` + small keys commit xong (không stamp trước), nên target vào split mode không bao giờ rơi vào trạng thái "đã bỏ blob nhưng split chưa publish xong".
- Phép đo chuyển sang process SP-X, đọc SharedPreferences local, không qua binder (`manager prefs bundle`).

## Quy tắc chung
**Cờ/gate điều khiển việc "có đọc payload X không" phải nằm NGOÀI payload X.** Nếu gate nằm trong X, mọi lần check gate đều phải đọc X — gate tự vô hiệu hoá chính nó. Áp dụng cho: migration flags, feature gates trên remote config blob, "đo kích thước" của chính cái đang đo.

## Check phòng
- Mọi key mà target đọc để QUYẾT ĐỊNH có pull group lớn không → grep xem nó nằm ở group nào; phải là group nhỏ/pull rẻ.
- Mọi hàm "đo" `.all`/`.getAll()` trên remote prefs trong target → hỏi: phép đo này có tự tạo ra pull mà nó đang đo không? Đo ở process ghi (local), không đo ở process đọc (binder).
- Review checklist: liệt kê mọi `getRemotePreferences(<group>)` trong target + kích thước ước lượng mỗi group; group nào > vài KB mà mọi process đều pull → cờ đỏ.
