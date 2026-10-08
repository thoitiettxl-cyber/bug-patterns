#!/usr/bin/env python3
"""Sinh lại bug-patterns/INDEX.md từ toàn bộ *.md (trừ INDEX.md, RULES.md).

Chạy:  python3 scripts/gen-index.py        (từ repo root)
Kiểm:  python3 scripts/gen-index.py --check (exit 1 nếu INDEX.md lệch)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "bug-patterns"
INDEX = BASE / "INDEX.md"

DOMAINS = ["android", "build", "kotlin", "process"]
SECTION_TITLE = {
    "android": "Android",
    "build": "Build",
    "kotlin": "Kotlin",
    "process": "Process",
    "root": "Chưa phân nhóm (nằm ở root — nên chuyển vào domain/)",
}

HEADER = """# Kho bug-patterns — bẫy đã biết, đừng mắc lại

Mỗi file = 1 bug pattern từng gây bug thật. Session mới làm việc với domain
tương ứng thì **đọc lesson trước khi code**. Khác với memory (lưu facts),
đây là kho *bẫy*: triệu chứng → root cause → fix → cách phòng bằng check
chạy được.

Quy ước: lesson nào cũng phải có mục **Phòng** — 1 câu lệnh hoặc 1 checklist
item có thể chạy/kiểm tra bằng máy. Lesson không có cách phòng thì chỉ là
chuyện kể.

> **Quy tắc theo nhóm:** xem [`RULES.md`](RULES.md) khi cần nhìn nhanh toàn bộ bẫy.
>
> File này được sinh tự động bằng `scripts/gen-index.py` — đừng sửa tay.
"""

FOOTER = """## Thêm pattern mới

1 bug = 1 file (hoặc 1 mục) ngay trong commit fix. Đặt tên file dạng
`domain/ten-pattern.md`, theo đúng format 5 mục trong các file hiện có.
Xong chạy `python3 scripts/gen-index.py` để cập nhật INDEX.
"""


def first_sentence(text: str, limit: int = 150) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    # Gỡ marker markdown: "- ", "**", "`", "> ", inline code
    text = re.sub(r"^[\s\-*>`]+", "", text)
    text = text.replace("`", "").replace("**", "").replace("*", "").strip()
    m = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    s = m[0]
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


def summarize(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = None
    symptom = None
    for i, ln in enumerate(lines):
        if title is None and ln.startswith("# "):
            title = ln[2:].strip()
        # Dạng: "- **Triệu chứng:** ..." | "Triệu chứng: ..." (+ gom cả đoạn)
        m = re.match(r"^\s*(?:[-*]\s*)?\*{0,2}Triệu chứng\*{0,2}\s*:\s*(.+)$", ln)
        if m and symptom is None:
            parts = [m.group(1)]
            for nxt in lines[i + 1 :]:
                s = nxt.strip()
                if not s or re.match(r"^#{1,4}\s|^[-*]\s+\*\*", s):
                    break
                parts.append(s)
            symptom = " ".join(parts)
        elif re.match(r"^#{2,3}\s*Triệu chứng\s*$", ln) and symptom is None:
            parts = []
            for nxt in lines[i + 1 :]:
                s = nxt.strip()
                if not s or re.match(r"^#{1,4}\s|^[-*]\s+\*\*", s):
                    break
                parts.append(s)
            symptom = " ".join(parts)
    desc = first_sentence(symptom) if symptom else (title or path.stem)
    return desc


def main() -> int:
    files = sorted(
        p for p in BASE.rglob("*.md") if p.name not in ("INDEX.md", "RULES.md")
    )
    groups: dict[str, list[Path]] = {d: [] for d in DOMAINS} | {"root": []}
    for p in files:
        rel = p.relative_to(BASE)
        key = rel.parts[0] if len(rel.parts) > 1 and rel.parts[0] in DOMAINS else "root"
        groups[key].append(p)

    out = [HEADER]
    total = 0
    for key in DOMAINS + ["root"]:
        items = groups[key]
        if not items:
            continue
        total += len(items)
        out.append(f"\n## {SECTION_TITLE[key]} ({len(items)})\n")
        for p in sorted(items, key=lambda x: x.relative_to(BASE).as_posix()):
            rel = p.relative_to(BASE).as_posix()
            out.append(f"- `{rel}` — {summarize(p)}")
    out.append(f"\n_Tổng: {total} pattern._\n")
    out.append("\n" + FOOTER)
    content = "\n".join(out)

    if "--check" in sys.argv:
        current = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if current != content:
            print(f"INDEX.md lệch: có {total} pattern, file hiện tại khác bản sinh.",
                  file=sys.stderr)
            return 1
        print(f"OK: INDEX.md khớp {total} pattern.")
        return 0

    INDEX.write_text(content, encoding="utf-8")
    print(f"Đã sinh INDEX.md: {total} pattern.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
