# ghidra-getaddress-null-not-throw — `AddressFactory.getAddress()` trả `null` chứ không throw khi address sai format

## Triệu chứng
- `ExportXrefs.java 0xZZZZ both` → **không** in dòng `ERROR: invalid address`
  như code dự định, mà nổ `NullPointerException` lên framework:
  `ERROR REPORT SCRIPT ERROR: (HeadlessAnalyzer) java.lang.NullPointerException:
  Cannot invoke "ghidra.program.model.address.Address.isStackAddress()"
  because "addr" is null` (tại `ReferenceDBManager.getReferencesTo`,
  gọi từ `ExportXrefs.run(ExportXrefs.java:68)`). Không có file JSON nào được ghi.
- `ExportDisassembly.java 0xZZZZ 0x0010d100` / `0xZZZZ` → may mắn hơn (NPE bị
  `catch (Exception)` nuốt) nhưng message user thấy là NPE thô, không nêu input
  lỗi: `ERROR: invalid address argument: Cannot invoke
  "ghidra.program.model.address.Address.compareTo(Object)" because "start" is
  null` / `...Address.isExternalAddress()... because "addr" is null`.
- Địa chỉ **parse được nhưng ngoài memory map** (`0xffffffffffff`) thì lại ổn:
  xrefs trả JSON rỗng `count: 0`, disasm báo `ERROR: no function contains
  address` — chứng tỏ chỉ nhánh "sai format" là gãy.

## Root cause
`currentProgram.getAddressFactory().getAddress(String)` với input không parse
được (`0xZZZZ`) **trả về `null`, không throw exception**. Cả hai script đều chỉ
bọc `getAddress()` trong `try/catch` mà không null-check:
- `ExportXrefs.java`: `addr = null` lọt qua catch → `refMgr.getReferencesTo(null)`
  → NPE văng ra ngoài `run()`, Ghidra báo SCRIPT ERROR, không file output.
- `ExportDisassembly.java`: `null.compareTo(end)` / `getFunctionContaining(null)`
  → NPE bị catch chung → message `invalid address argument: <NPE text>` gây
  hiểu lầm (nghe như lỗi internal, không chỉ ra arg nào sai).

## Fix (đề xuất — chưa apply, chờ Boss/coordinator quyết)
Sau mỗi `getAddress(...)`, thêm null-check tường minh trước khi dùng:
```java
addr = currentProgram.getAddressFactory().getAddress(addrStr);
if (addr == null) {
    println("ERROR: invalid address '" + addrStr + "'");
    return;
}
```
Áp dụng cho cả 3 call site trong `ExportDisassembly.java` (start, end, single)
và 1 call site trong `ExportXrefs.java`. Giữ nguyên `try/catch` cho các lỗi
khác (ví dụ overflow vẫn có thể throw).

## Check (chạy được)
```sh
cd ~/workspace/skills/ghidra
BIN=/home/hatch/workspace/skills/mcp/.venv/lib/python3.12/site-packages/_cffi_backend.cpython-312-x86_64-linux-gnu.so
./scripts/ghidra-analyze.sh --no-analysis -s ExportXrefs.java -a "0xZZZZ both" -o /tmp/gz "$BIN" 2>&1 | grep -E "ERROR|NullPointer"
# kỳ vọng sau fix: dòng "ERROR: invalid address '0xZZZZ'", KHÔNG còn NullPointerException
```
Phát hiện trong smoke test worker B chiến dịch ghidra-smoke-final
(2026-10-06): evidence tại
`~/workspace/skills/ghidra/.campaign/smoke/workerB-smoke-result.md`
(runs `e1`, `e8`, `e9`).
