from collections import Counter
from pathlib import Path
import re
import sys

SUFFIXES = {".md", ".txt"}

# 统计高频词用的切分规则：英文/数字按词，中文按单字。
# 不做真正的分词（不引入 jieba），但中文不再整串算一个词。
TOKEN_RE = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]")


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
    # words 仍是「按空白切分的词数」；top_words 用 TOKEN_RE，中文按单字统计
    tokens = TOKEN_RE.findall(text.lower())
    pairs = sorted(Counter(tokens).items(), key=lambda kv: (-kv[1], kv[0]))
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