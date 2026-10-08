# split rồi trim: phải trim MỌI tầng split, không chỉ tầng ngoài

Triệu chứng: parse rule/config bằng nhiều tầng `split` lồng nhau (`:` rồi `/`
rồi `,`). Fix trim whitespace chỉ áp ở tầng ngoài → tầng trong vẫn giữ
whitespace → exact-match ở consumer rớt lặng lẽ.

Case thật (2026-09-30, MyInjector smoke test): commit `79680df` thêm
`.map { it.trim() }` sau các split `:`/`,` trong `commitSystem()` nhưng BỎ SÓT
2 split `/` tách package/component (SettingsActivity.kt ~1104/1114).
Rule `"com.a / MyActivity"` → `sourcePackage = "com.a "` → system_server so
`==` rớt. Chính code-review skill (Q3) bắt được; fix ở `edf3018`; verify bằng
Python port 4/4.

Root cause: khi viết fix, mắt chỉ quét các split cùng "hình dạng" với bug gốc
(`:`/`,`), bỏ qua split khác delimiter trong cùng hàm.

Phòng:
- Sau khi thêm trim/normalize, `grep -n "split(" <file>` liệt kê TẤT CẢ split
  trong hàm và check từng cái.
- Viết test/port logic với case có whitespace ở MỌI vị trí phân tách, không chỉ
  vị trí trong bug report gốc.
