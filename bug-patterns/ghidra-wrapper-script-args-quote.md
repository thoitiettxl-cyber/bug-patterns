# ghidra-wrapper-script-args-quote — quote trong `-a` đi nguyên vào regex của script

## Triệu chứng
- Chạy đúng example trong SKILL.md:
  `ghidra-analyze.sh -s SearchStrings.java -a '"Error.*failed" 6' -o ./output binary`
  → `SearchStrings` tìm **0 match** dù binary có string chứa `Error...failed`.
- JSON output ghi `"regex": "\"Error.*failed\""` — regex thực tế có quote
  `"` ở hai đầu (literal), không phải `Error.*failed` như user nghĩ.
- Sai thầm lặng: không báo lỗi, exit 0, user tưởng binary không có match.

## Root cause
`scripts/ghidra-analyze.sh` ghép args bằng unquoted expansion:
```bash
CMD+=($args)   # ghidra-analyze.sh
```
Word-splitting KHÔNG strip quote (quote removal chỉ xảy ra khi shell parse
literal command line, không áp dụng cho kết quả expansion). Nên argv tới
`analyzeHeadless` vẫn giữ nguyên ký tự `"`: args[0] của GhidraScript là
`"Error.*failed"` (có quote). SKILL.md document example với quote vì cần
quote để outer shell giữ `'"Error.*failed" 6'` thành 1 giá trị `-a` — nhưng
wrapper không strip lại lớp quote đó trước khi forward.

## Fix (đề xuất — chưa apply, chờ Boss/coordinator quyết)
1. Đơn giản nhất, không đụng wrapper: sửa SKILL.md — mọi example `-a`
   bỏ quote trong: `-a 'Error.*failed 6'`, và ghi chú `-a` dùng
   word-splitting nên pattern có space không được hỗ trợ.
2. Hoặc wrapper strip 1 lớp quote bao quanh mỗi element sau khi split
   (cẩn thận pattern có space: `'"Error failed" 6'` split thành 3 element
   → strip từng element vẫn gãy; cần parse tử tế hơn `eval` — `eval`
   nguy hiểm, không khuyến nghị).
3. SearchStrings.java có thể warn khi regex bắt đầu/kết thúc bằng `"`
   (heuristic rẻ, nhưng không fix root cause).

## Check (chạy được)
```sh
cd ~/workspace/skills/ghidra
BIN=/home/hatch/workspace/skills/mcp/.venv/lib/python3.12/site-packages/_cffi_backend.cpython-312-x86_64-linux-gnu.so
# trước fix: JSON ghi regex có quote
./scripts/ghidra-analyze.sh -s SearchStrings.java -a '"ThreadCanary" 6' -o /tmp/q1 "$BIN"
python3 -c "import json;print(repr(json.load(open([f for f in __import__('glob').glob('/tmp/q1/*_searchstrings.json')][0]))['regex']))"
# kỳ vọng sau fix (option 1: doc đúng): regex == 'ThreadCanary', không có quote
```
Phát hiện trong smoke test worker C chiến dịch ghidra-smoke-final
(2026-10-06): evidence tại
`~/workspace/skills/ghidra/.campaign/smoke/workerC-smoke-result.md`.
