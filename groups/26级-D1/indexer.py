from collections import Counter
from pathlib import Path
import sys

SUFFIXES = {".md", ".txt"}


def iter_files(root):
    base = Path(root)
    if not base.is_dir():
        print(f"目录不存在：{root}", file=sys.stderr)
        sys.exit(1)
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUFFIXES:
            yield path


def analyze_file(path, top_n=5, base=None):
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        print(f"警告：跳过 {path}({exc.__class__.__name__})", file=sys.stderr)
        return None
    words = text.lower().split()
    pairs = sorted(Counter(words).items(), key=lambda kv: (-kv[1], kv[0]))
    rel = path.relative_to(base).as_posix() if base else path.as_posix()
    return {
        "path": rel,
        "lines": len(text.splitlines()),
        "words": len(words),
        "chars": len(text),
        "top_words": [list(kv) for kv in pairs[:top_n]],
    }


def build_index(root, top_n=5):
    base = Path(root)
    files = [item for p in iter_files(root) if (item := analyze_file(p, top_n, base))]
    return {"root": root, "files": files}