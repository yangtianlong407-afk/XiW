import argparse
import json
import sys
from pathlib import Path

import indexer
import searcher

# index.json 固定放在脚本旁边：在哪个目录敲命令都找得到，不用先 cd 回项目目录
INDEX_PATH = Path(__file__).resolve().parent / "index.json"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="minisearch")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="遍历目录，写出 index.json")
    p_index.add_argument("root", help="要索引的根目录")
    p_index.add_argument("--top", type=int, default=5, help="每个文件保留几个高频词，默认 5")
    p_index.add_argument("--json", action="store_true", help="用 JSON 打印结果，给程序读")

    p_search = sub.add_parser("search", help="在索引里查关键词")
    p_search.add_argument("root", help="建索引时用的那个根目录")
    p_search.add_argument("keyword", help="要查的词")
    p_search.add_argument("--json", action="store_true", help="用 JSON 打印结果，给程序读")

    args = parser.parse_args(argv)

    if args.command == "index":
        data = indexer.build_index(args.root, args.top)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        if args.json:
            print(json.dumps(
                {"command": "index", "root": args.root, "index": "index.json",
                 "files": len(data["files"])},
                ensure_ascii=False, indent=2))
        else:
            print(f"索引 {len(data['files'])} 个文件 → index.json")
        return 0

    if not INDEX_PATH.exists():
        print("请先运行 index 建立索引", file=sys.stderr)
        return 1

    if not args.keyword.strip():
        print("关键词不能为空", file=sys.stderr)
        return 2

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    hits = searcher.search(data, args.keyword, base=INDEX_PATH.parent)
    if args.json:
        print(json.dumps(
            {"command": "search", "root": args.root, "keyword": args.keyword,
             "count": len(hits),
             "hits": [{"path": path, "count": n, "line": line} for path, n, line in hits]},
            ensure_ascii=False, indent=2))
    else:
        print(searcher.format_hits(hits))
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
