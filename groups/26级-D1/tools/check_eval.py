"""开发辅助：只跑检索，检查 eval.md 里「期望出处」能不能被搜出来。

它不调模型、不花钱，用来在花钱之前先确认题目出得对。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ask  # noqa: E402


def parse_rows(md_text):
    rows = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"编号", "#"}:
            continue
        rows.append(cells)
    return rows


def main():
    eval_path = Path(sys.argv[1] if len(sys.argv) > 1 else "eval.md")
    index = ask.load_index(sys.argv[2] if len(sys.argv) > 2 else "index.json")
    if index is None:
        return 1

    rows = parse_rows(eval_path.read_text(encoding="utf-8"))
    if not rows:
        print("没解析到表格行，检查 eval.md 的表格格式")
        return 1

    ok = bad = skip = 0
    print(f"{'编号':<4}{'类型':<8}{'结果':<10}期望出处 / 实际取到")
    print("-" * 78)
    for cells in rows:
        no, question = cells[0], cells[1]
        kind = cells[2] if len(cells) > 2 else ""
        expected = cells[3] if len(cells) > 3 else ""
        want = re.findall(r"docs/[^\s:：|]+\.md:\d+", expected)
        passages = ask.find_passages(index, question, 3)
        got = [f"{p}:{n}" for p, n, _ in passages]
        if not want:
            skip += 1
            print(f"{no:<4}{kind:<8}{'跳过':<10}(该题不要求具体出处)")
            continue
        hit = all(w in got for w in want)
        if hit:
            ok += 1
        else:
            bad += 1
        mark = "OK" if hit else "未命中"
        print(f"{no:<4}{kind:<8}{mark:<10}期望 {'、'.join(want)} | 实际 {'、'.join(got) or '无'}")

    print("-" * 78)
    print(f"命中 {ok} 条，未命中 {bad} 条，跳过 {skip} 条")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

