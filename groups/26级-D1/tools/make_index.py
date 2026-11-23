"""开发辅助：扫描 docs/ 生成 index.json（字段与 W2 任务书一致）。

组里已经有 A 的 indexer.py 时，用他们的 minisearch.py index docs/ 即可；
这个脚本只是为了本地没有 A 的代码时也能把 W3 跑起来。
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = sys.argv[1] if len(sys.argv) > 1 else "docs"
OUT = sys.argv[2] if len(sys.argv) > 2 else "index.json"
SUFFIXES = {".md", ".txt"}


def analyze(path: Path, base: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        print(f"警告：跳过 {path}（{exc.__class__.__name__}）", file=sys.stderr)
        return None
    words = re.findall(r"[a-z0-9_]+", text.lower())
    chars = re.findall(r"[\u4e00-\u9fff]", text)   # 中文按单字统计，与任务书一致
    counts = Counter(words + chars)
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "path": path.relative_to(base).as_posix(),
        "lines": len(text.splitlines()),
        "words": len(text.lower().split()),
        "chars": len(text),
        "top_words": top,
    }


def main():
    base = Path(ROOT)
    files = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUFFIXES:
            item = analyze(path, base)
            if item:
                files.append(item)
    data = {"root": ROOT, "files": files}
    Path(OUT).write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"索引 {len(files)} 个文件 → {OUT}")


if __name__ == "__main__":
    main()
