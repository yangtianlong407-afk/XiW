from pathlib import Path


def search(index, keyword, base=None):
    """返回 [(显示路径, 次数, 第一处匹配行), ...]，按次数降序、同次数按路径升序。

    base：可选的根目录。index 里存的是相对路径（如 docs），
    传了 base 就按 base 去读文件，显示路径仍然是 docs/xxx.md 这种相对形式。
    """
    key = keyword.lower()
    shown_root = str(index["root"]).rstrip("/\\")
    root = Path(shown_root)
    if base is not None and not root.is_absolute():
        root = Path(base) / root
    hits = []
    for item in index["files"]:
        path = root / item["path"]
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        text = "\n".join(lines)
        n = text.lower().count(key)
        if not n:
            continue

        first = ""
        for line in lines:
            if key in line.lower():
                first = line.strip()[:80]
                break

        hits.append((f"{shown_root}/{item['path']}", n, first))

    hits.sort(key=lambda x: (-x[1], x[0]))
    return hits


def format_hits(hits):
    if not hits:
        return "没有找到"

    out = []
    for path, n, line in hits:
        out.append(f"{path}: {n}")
        if line:
            out.append(f"  {line}")
    return "\n".join(out)
