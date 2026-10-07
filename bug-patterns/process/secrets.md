# Không bao giờ "tái tạo" secret từ trí nhớ

- **Triệu chứng:** Pi từng định tái tạo tunnel token từ trí nhớ thay vì copy
  nguyên văn → suýt đưa token sai vào config. (E-Muse.)
- **Root cause:** secret là chuỗi ngẫu nhiên, trí nhớ không đáng tin; tái tạo
  = tạo ra secret sai mà trông như đúng.
- **Fix — luật cứng:** secret chỉ copy nguyên văn từ file nguồn
  (`hidden/tunnel_token.txt` mode 600, gitignored). Không ghi giá trị thô
  vào chat, memory, repo public, lesson. Config trong repo chỉ giữ
  placeholder `${VAR}`.
- **Phòng:** trước khi paste secret, kiểm tra: nguồn là file gốc? Nếu phải
  "nhớ lại" → dừng, tìm file gốc.
- **Nguồn:** E-Muse 2026-09-29; `~/AGENTS.md` mục Secrets.
