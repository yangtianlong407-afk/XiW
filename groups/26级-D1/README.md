# minisearch

三人合作的迷你全文检索工具：给一个目录建一张索引表，再按关键词查这张表。

- 组别：D1　｜　代码目录：`groups/26级-D1/`
- 运行环境：Python 3.12（只用标准库：`pathlib`、`json`、`argparse`、`collections`），Windows + PowerShell
- 不需要安装任何第三方包

## 目录结构

```
groups/26级-D1/
├── minisearch.py     命令行入口（argparse + 调用下面两个模块）
├── indexer.py        遍历目录、统计、生成索引
├── searcher.py       查关键词、拼输出
├── README.md         本文件：字段表 + 用法
├── scope.md          这个工具做什么、不做什么
├── tests.md          8 条测试与真实输出
└── review.md         交叉互评记录
```

演示素材放在仓库的 `docs/`，测试素材放在 `tests/fixtures/`（都不属于代码目录）。

## 三条命令

在 `groups/26级-D1/` 下执行：

```powershell
python minisearch.py index docs              # 建索引，写出 index.json
python minisearch.py search docs python      # 查关键词
python minisearch.py index docs --top 10     # 每个文件保留 10 个高频词（默认 5）
```

真实输出（`python minisearch.py index docs`）：

```
索引 2 个文件 → index.json
```

真实输出（`python minisearch.py search docs python`）：

```
docs/notes.txt: 2
  python 处理文件
```

## index.json 字段（v1，已冻结）

```json
{
  "root": "docs",
  "files": [
    {
      "path": "guide/intro.md",
      "lines": 2,
      "words": 4,
      "chars": 29,
      "top_words": [["minisearch", 1], ["入门", 1], ["是一个迷你全文检索工具。", 1]]
    },
    {
      "path": "notes.txt",
      "lines": 2,
      "words": 4,
      "chars": 29,
      "top_words": [["python", 2], ["处理文件", 1], ["也可以写脚本来统计", 1]]
    }
  ]
}
```

| 字段 | 类型 | 含义 | 示例 |
| --- | --- | --- | --- |
| `root` | 字符串 | 建索引时传入的那个目录（原样记录） | `"docs"` |
| `files` | 数组 | 每个被索引的文件一项 | `[...]` |
| `files[].path` | 字符串 | **相对 `root`** 的路径，统一用 `/` 分隔 | `"guide/intro.md"` |
| `files[].lines` | 整数 | 行数（`splitlines()` 的结果） | `2` |
| `files[].words` | 整数 | 词数（小写后按空白切分） | `4` |
| `files[].chars` | 整数 | 字符数（`len(文本)`） | `29` |
| `files[].top_words` | 数组 | `[[词, 次数], ...]`，次数降序、同次数按词升序 | `[["python", 2]]` |

**冻结规则**：这张表定下来之后不再改动。要加字段、改名、改类型，先在群里说、三个人同意、改本文件、再改代码。`index.json` 由程序生成，**不手工编辑**。

## 搜索输出格式

每个命中的文件占两行：

1. 第一行：`路径: 次数`（路径是 `root` + 索引里的 `path`，用 `/` 分隔）
2. 第二行：两个空格缩进的第一处匹配行（原文 `strip()` 后，超过 80 字截断；该文件没有可显示的行时省略）

文件之间按命中次数降序，同次数按路径升序。没有命中时只打印一行 `没有找到`。

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功：索引写好了，或者搜索有命中 |
| `1` | 目录不存在 / 还没建索引 / 搜索没有命中 |
| `2` | 参数错误（`argparse` 自动给出，例如没写子命令） |

## 已知限制

- 中文不分词。`words` 按空白切分，所以一整段中文只算 1 个词；`top_words` 里出现的中文条目也是整串。`search` 的关键词匹配是子串包含，中文可以正常查。
- 只索引 `.md` 和 `.txt` 两种后缀，其余文件跳过。
- 非 UTF-8 文件会被跳过，并在 stderr 打一行警告，**不中断**整次索引。
- 大文件是全量读进内存再统计的，超大目录会慢、会占内存。
- `search` 依赖当前目录下的 `index.json`，换目录要先重新 `index`。
