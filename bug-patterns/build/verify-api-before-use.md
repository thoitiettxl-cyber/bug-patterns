# Verify API/compile trước khi dùng — cấm đoán

- **Triệu chứng:** Build fail hoặc runtime crash vì dùng API không tồn tại/
  không đúng: `java.lang.ProcessHandle` (không có trên Android SDK), API
  Miuix/TextField/icons sai, built-in Kotlin của AGP 9.x đổi, package CI
  `platforms;android-37` sai. (E-Muse, nhiều lần 2026-09-29/30.)
- **Root cause:** đoán API từ trí nhớ/training data thay vì tra docs mới nhất.
- **Fix — luật cứng của Boss (2026-09-29):** mọi claim liên quan compile/API
  phải verify qua **Context7** (resolve-library-id cần cả `libraryName` +
  `query`) và/hoặc web search trước khi viết code. Ghi trong `~/AGENTS.md`.
- **Phòng:** khi agent đề xuất 1 API mới (đặc biệt Miuix/Compose/AGP), hỏi
  ngược: "đã tra Context7 chưa?" Nếu chưa → chưa được viết code.
- **Nguồn:** E-Muse 2026-09-29/30, nhiều commit fix compile.
