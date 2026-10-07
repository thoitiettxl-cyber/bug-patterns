# Quick Tunnel không đáng tin trên mọi máy/mạng

- **Triệu chứng:** Quick Tunnel (URL random) không nối được: QUIC và HTTP/2
  đều fail trên máy Boss. (E-Muse, 2026-09-29.)
- **Root cause:** Quick Tunnel phụ thuộc edge ngẫu nhiên + QUIC; một số mạng/
  máy chặn QUIC → tunnel chết không rõ lý do.
- **Fix:** chuyển đường chính sang **named tunnel** (token + hostname cố định,
  URL không đổi). Quick Tunnel chỉ là fallback. Thêm toggle "Domain cố định"
  cho user chọn (E-Muse `3421ae9`).
- **Phòng:** tính năng nào cần URL ổn định (MCP endpoint cho agent gọi từ xa)
  → mặc định named tunnel, đừng mặc định quick.
- **Nguồn:** E-Muse 2026-09-29, commit `3421ae9`.
