# minisearch + ask.py

三人合作的迷你全文检索工具：给一个目录建一张索引表，再按关键词查这张表。
W3 在它上面加了一张「嘴」：把检索结果交给大模型，只按资料回答并标出处。

- 组别：D1　｜　代码目录：`groups/26级-D1/`
- 运行环境：Python 3.9 及以上（开发与实测在 3.12 上做的，代码没有用 3.9 之后的新语法），Windows + PowerShell
- W2 只用标准库；W3 可选 `requests`——没装也能跑，会自动退回标准库 `urllib`
- W3 起需要一个大模型 key（DeepSeek / 通义 / 智谱任选，OpenAI 兼容即可）

## 目录结构

```
groups/26级-D1/
├── minisearch.py     命令行入口（argparse + 调用下面两个模块）
├── indexer.py        遍历目录、统计、生成索引
├── searcher.py       查关键词、拼输出
├── ask.py            W3：检索 + 调大模型 + 输出答案与出处
├── api.md            W3：接口说明（输入/输出/退出码/错误）
├── eval.md           W3：10 条评测题与真实输出
├── 错误处理记录.md    W3：五条错误的实测输出（命令/退出码/stdout/stderr）
├── 跑通记录.md       胡轩也照本 README 独立跑一遍的记录与提出的卡点
├── README.md         本文件
├── scope.md          这个工具做什么、不做什么
├── tests.md          9 条测试与真实输出
├── review.md         交叉互评记录
├── requirements.txt  W3 依赖（requests，可选）
├── tools/            开发辅助：验题、造素材、假模型、一键助手
└── docs/             演示语料（含 scope.md 副本与两条边界素材）
```

测试素材放在 `tests/fixtures/`。

## W2：三条命令

在 `groups/26级-D1/` 下执行：

```powershell
python minisearch.py index docs              # 建索引，写出 index.json
python minisearch.py search docs python      # 查关键词
python minisearch.py index docs --top 10     # 每个文件保留 10 个高频词（默认 5）
python minisearch.py index docs --json       # 给程序读：只打印一个 JSON 对象
python minisearch.py search docs python --json
```

`index.json` 固定放在**脚本所在目录**，`docs/` 也相对脚本目录解析，
所以不在这个目录里也能跑，输出里的路径仍然是 `docs/notes.txt: 2` 这种相对形式：

```powershell
cd C:\
python D:\D1\groups\26级-D1\minisearch.py search docs python
```

真实输出（`python minisearch.py index docs`）：

```
索引 4 个文件 → index.json
```

`docs/` 里有 5 个文件，其中 `docs/gbk.txt` 是 GBK 编码，读不了会被跳过，
**所以显示 4 个**，stderr 会多一行警告：

```
警告：跳过 docs\gbk.txt(UnicodeDecodeError)
```

跳过不算失败，退出码仍是 `0`；被跳过的文件不会出现在 `index.json` 里。

真实输出（`python minisearch.py search docs python`）：

```
docs/notes.txt: 2
  python 处理文件
docs/scope.md: 1
  - 一个目录（可以有任意层子目录），例如 `python minisearch.py index docs`
```

真实输出（`python minisearch.py search docs python --json`）：

```json
{
  "command": "search",
  "root": "docs",
  "keyword": "python",
  "count": 2,
  "hits": [
    {"path": "docs/notes.txt", "count": 2, "line": "python 处理文件"},
    {"path": "docs/scope.md", "count": 1, "line": "- 一个目录（可以有任意层子目录），例如 `python minisearch.py index docs`"}
  ]
}
```

`--json` 时 stdout 只有那一个 JSON 对象，提示与警告一律走 stderr；退出码与文本模式相同。

## W3：ask.py

```powershell
$env:LLM_API_KEY="你的key"
$env:LLM_BASE_URL="https://api.deepseek.com"   # 可选
$env:LLM_MODEL="deepseek-chat"                 # 可选

python ask.py ask "典型使用场景是什么？"
python ask.py ask "典型使用场景是什么？" --json
python ask.py ask "典型使用场景是什么？" --offline   # 不联网，只打印将要发送的 Prompt
```

`--offline` 用来检查 Prompt 拼得对不对：把将要发给模型的内容原样打印出来，
但**不读 key、不发请求、不花钱**，改 Prompt 时先看它最省事。

没装 `requests` 不影响使用：`ask.py` 会自动退回标准库 `urllib`，回答、退出码、
错误提示都和装了的时候一样，只在 stderr 多一行提示。装上更好（`pip install -r requirements.txt`），
超时和异常分类更细。

真实输出：

```
典型使用场景是：作业写完了想确认「某个词到底在哪个文件里出现过」，或者「哪份文档里出现得最多」。(docs/scope.md:8)

来源：docs/scope.md:8、docs/scope.md:25
```

流程：读 `index.json` → 关键词检索取前 3 行 → 与 `file:line` 一起拼进 Prompt → 调 chat completions
→ 输出答案与来源；**检索零命中时直接回答「文档里没有」，不调用模型**。

接口、错误码见 [`api.md`](api.md)；五条错误的实测输出（命令、退出码、stdout/stderr 分栏）见
[`错误处理记录.md`](错误处理记录.md)；10 条评测见 [`eval.md`](eval.md)。

评测想自己复跑一遍：配好 `LLM_API_KEY` 后在本目录执行 `python tools\wizard.py`，选第 2 步，
脚本会真调模型把 10 条题重新跑一遍，生成 `eval-filled.md`（表格填好的版本）和 `评测输出.txt`（原始输出）。
没有 key 时可以先跑 `python tools\check_eval.py eval.md index.json`，只验证「期望出处能不能被检索命中」，不花钱。

## 评测（测出来的结论）

10 条：5 条能答、3 条该拒答、2 条边界。每条都带 `file:line` 出处。

```powershell
python tools\check_eval.py eval.md index.json   # 只验检索，不花钱
python tools\wizard.py                          # 1 准备 / 2 评测 / 3 错误处理
```

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功：索引写好了 / 搜索有命中 / 问题得到回答或正确拒答 |
| `1` | 目录不存在、还没建索引、没有命中、缺 key、网络或模型报错 |
| `2` | 参数错误（`argparse` 自动给出） |

## 已知限制

- 中文不做分词，`top_words` 只到单字：英文/数字按词统计，中文每个字算一条，`words` 仍按空白切分。`search` 用子串包含，中文词组能查。
- 只索引 `.md` 和 `.txt`，非 UTF-8 文件跳过并在 stderr 警告，不中断。
- 检索是「中文两字组合 + 命中行数」排序，不是向量检索；换个说法可能搜不到。
- 每类资料只取前 3 行，答案跨段落时可能漏。
- 大目录全量读进内存；`index.json` 固定在脚本目录，与当前工作目录无关。
