# Kotlin — bảng opcode copy từ upstream, comment "verified" nhưng sai 32 entry

Triệu chứng: T1 (bytecode dataflow fallback) CI xanh, review pass, nhưng layer-2
chạy trên instruction trace LỆCH từ instruction `23x` đầu tiên (`add-int`…)
trong mọi method — kết quả dataflow sai âm thầm, không crash nên không ai hay.

Root cause: `opCodeWide[0x90..0xaf]` = 2 trong khi AOSP Dalvik bytecode quy định
23x (three-register ops: add-int/sub-int/…/rem-double) width = **3** code units.
Bảng port từ MyInjector (upstream đã sai), comment trên bảng ghi "verified
against the current dex format" — verify bằng mắt, không chạy script so với
AOSP. Audit team viết script so live AOSP: 32/32 entry sai.

Fix: 32 entry → 3 + sửa comment ghi rõ `0x90..0xaf (23x) = 3` và note lịch sử
sai. (SpoofX `dev-codex`, audit 2026-10-04, finding P1-1.)

Phòng:
- Mọi bảng tra cứu port từ nguồn khác: viết script verify tự động so với
  source authoritative (AOSP/dexlib2), KHÔNG verify bằng mắt. Comment "verified"
  phải kèm CÁCH verify (script/link), không thì coi như chưa verify.
- Bảng số mà sai 1 entry là lệch toàn bộ parse phía sau — đây là lớp bug
  "silent corruption", ưu tiên viết test so snapshot với nguồn chuẩn.
