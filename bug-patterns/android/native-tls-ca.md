# Binary Go/native không đọc system CA store của Android

- **Triệu chứng:** cloudflared (Go) chạy trên Android báo lỗi TLS dù máy vào
  https bình thường. (E-Muse fix `616cd69`.)
- **Root cause:** Go TLS stack không đọc Android system CA store → không tin
  bất kỳ CA nào → handshake fail.
- **Fix:** bundle Mozilla CA (`cacert.pem`) vào app, export `SSL_CERT_FILE`
  trỏ tới bundle khi spawn process Go.
- **Phòng:** bất kỳ binary native/Go nào làm TLS trên Android → mặc định phải
  có CA bundle riêng. Check trong code spawn process: có set `SSL_CERT_FILE`
  không.
- **Nguồn:** E-Muse commit `616cd69`.
