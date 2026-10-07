# param.result = null không guard returnType → unbox NPE (H-P1-2)

- **Triệu chứng:** (tiềm ẩn) `param.result = null` trong `hookBefore` của method
  mà matcher không constrain returnType → nếu target đổi signature trả primitive,
  framework unbox null → NPE → crash target process (vi phạm "never crash").
  (SpoofX FacebookAdsRemover, audit 2026-10-05.)
- **Root cause:** `FacebookAdsResolver.resolveGameAdBridgePostMessageMethod` chỉ
  match name/parameterCount/paramTypes, không check returnType; `hookGameAdBridge`
  gán `param.result = null` ở cả 2 nhánh.
- **Fix:** Branch theo `method.returnType` như `hookGameAdActivityLaunchMethod` đã
  làm: boolean→false, int→0, long→0L, float→0f, double→0.0, char→'\u0000',
  byte→0.toByte(), short→0.toShort(), còn lại→null. (Review pass 1 bắt thiếu
  6/8 primitive — guard nửa vời vẫn NPE.)
- **Check chạy được:** source-shape test assert không còn `param.result = null`
  trần trong hook có matcher không constrain returnType; máy thật với FB build
  hiện tại (void) → behavior không đổi.
