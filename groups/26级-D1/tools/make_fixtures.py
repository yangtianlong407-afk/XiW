"""生成两条边界测试素材：空文件、非 UTF-8 文件。

用法：python tools/make_fixtures.py docs
"""

import sys
from pathlib import Path


def main():
    docs = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "empty.md").write_bytes(b"")
    (docs / "gbk.txt").write_bytes("中文测试内容".encode("gbk"))
    print(f"已生成 {docs/'empty.md'}（0 字节）和 {docs/'gbk.txt'}（GBK 编码）")


if __name__ == "__main__":
    main()
