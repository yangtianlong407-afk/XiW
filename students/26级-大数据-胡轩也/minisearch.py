import json
import re
import sys
from pathlib import Path


def iter_files(root: Path):
    """递归遍历目录下所有 .txt / .md，按路径排序返回；目录不存在则退出码 1。"""
    if not root.is_dir():
        print(f"目录不存在：{root}")
        sys.exit(1)
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".txt", ".md"}
    )


def analyze_file(path: Path):
    """统计单个文件：行数 / 词数 / 字符数 / Top5 高频词。
    非 UTF-8、无权限、读取失败 → 打 stderr 警告并返回 None（跳过，不中断）。"""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"警告：跳过非 UTF-8 文件 {path}", file=sys.stderr)
        return None
    except PermissionError:
        print(f"警告：无权限读取 {path}", file=sys.stderr)
        return None
    except OSError:
        print(f"警告：读取失败 {path}", file=sys.stderr)
        return None

    # 英文按单词（转小写）统计，中文按单字统计
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower()) + re.findall(r"[\u4e00-\u9fff]", text)
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "lines": len(text.splitlines()),
        "words": len(tokens),
        "chars": len(text),
        "top_words": [[w, c] for w, c in top],
    }


def build_index(root: Path, out_path: Path):
    """遍历目录生成 index.json（ensure_ascii=False, indent=2, sort_keys=True）。"""
    files = iter_files(root)
    entries = []
    for f in files:
        info = analyze_file(f)
        if info is not None:
            info["path"] = str(f.relative_to(root))
            entries.append(info)
    entries.sort(key=lambda e: e["path"])
    index = {"root": root.name, "files": entries}
    out_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
    if not entries:
        print("索引 0 个文件")
    return index
if __name__ == "__main__":
    files = iter_files(Path("."))
    print("找到的文件列表：")
    for f in files:
        print(f)
