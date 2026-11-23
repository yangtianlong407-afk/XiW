# tests.md — 8 条测试与真实输出

测试环境：Windows 11 + PowerShell，Python 3.12.14，仓库 `groups/26级-D1/`。
下面每条的「实际输出」都是**从终端整段复制**的，不是手打的。命令都在 `groups/26级-D1/` 下执行。

## 先准备素材（只做一次）

```powershell
cd D:\D1\groups\26级-D1
New-Item -ItemType Directory -Path docs\guide, tests\fixtures -Force
@("# 入门", "minisearch 是一个迷你全文检索工具。") | Out-File docs\guide\intro.md -Encoding utf8
@("python 处理文件", "python 也可以写脚本来统计") | Out-File docs\notes.txt -Encoding utf8
Copy-Item scope.md docs\scope.md -Force          # W3 评测语料：scope.md 的副本（行号必须和根目录那份一致）
New-Item -ItemType File docs\empty.md            # W3 边界素材：空文件
New-Item -ItemType File tests\fixtures\empty.txt
"中文测试" | Out-File tests\fixtures\gbk.txt -Encoding oem
Get-ChildItem -Recurse docs, tests | Select-Object FullName, Length
```

`docs/` 里因此有 4 个可索引文件（`guide/intro.md`、`notes.txt`、`scope.md`、`empty.md`）和 1 个非 UTF-8 的 `gbk.txt`；后者每次跑 `index` 都会在 stderr 打一行警告，这是预期行为。

`-Encoding oem` 写出来的是本机代码页（中文 Windows 上是 GBK），用来测「非 UTF-8」那一条。

---

## 1. 正常：索引一个含子目录的目录

**命令**

```powershell
python minisearch.py index docs
```

**期望**：4 个可读文件都被收进索引（`gbk.txt` 跳过），`docs/guide/intro.md` 的 `path` 是相对 `docs` 的 `guide/intro.md`

**实际输出**

```
索引 4 个文件 → index.json
```

**结论**：通过

---

## 2. 正常：同一个词出现多次，次数要对

**命令**

```powershell
python minisearch.py search docs python
```

**期望**：`notes.txt` 里 `python` 出现 2 次，第二行给出第一处匹配原文；`docs/scope.md` 的示例命令里也出现过 1 次

**实际输出**

```
docs/notes.txt: 2
  python 处理文件
docs/scope.md: 1
  - 一个目录（可以有任意层子目录），例如 `python minisearch.py index docs`
```

**结论**：通过

---

## 3. 中文关键词能搜到（子目录里的文件）

**命令**

```powershell
python minisearch.py search docs 检索
```

**期望**：命中 `docs/guide/intro.md`，并给出那一行原文

**实际输出**

```
docs/guide/intro.md: 1
  minisearch 是一个迷你全文检索工具。
```

**结论**：通过（中文不分词，但子串包含能命中）

---

## 4. 搜不到：打印「没有找到」，退出码 1

**命令**

```powershell
python minisearch.py search docs zzzz
echo "exit=$LASTEXITCODE"
```

**期望**：只打印一行 `没有找到`，退出码 1

**实际输出**

```
没有找到
exit=1
```

**结论**：通过

---

## 5. 异常：目录不存在，退出码 1

**命令**

```powershell
python minisearch.py index no-such-dir
echo "exit=$LASTEXITCODE"
```

**期望**：错误信息走 stderr，退出码 1，不生成 `index.json`

**实际输出**

```
目录不存在：no-such-dir
exit=1
```

**结论**：通过

---

## 6. 异常：空目录 → 索引 0 个文件

**命令**

```powershell
New-Item -ItemType Directory -Path tests\empty_dir -Force
python minisearch.py index tests/empty_dir
echo "exit=$LASTEXITCODE"
```

**期望**：正常结束，退出码 0，`index.json` 里 `files` 是空数组

**实际输出**

```
索引 0 个文件 → index.json
exit=0
```

**结论**：通过

---

## 7. 异常：空文件记 0，非 UTF-8 文件跳过并警告而不中断

**命令**

```powershell
python minisearch.py index tests/fixtures
echo "exit=$LASTEXITCODE"
Get-Content index.json
```

**期望**：`empty.txt` 被收录且五项都是 0/空；`gbk.txt` 不出现在索引里，stderr 有一行警告；退出码 0

**实际输出**

```
索引 1 个文件 → index.json
警告：跳过 tests\fixtures\gbk.txt(UnicodeDecodeError)
exit=0
```

`index.json` 的内容：

```json
{
  "files": [
    {
      "chars": 0,
      "lines": 0,
      "path": "empty.txt",
      "top_words": [],
      "words": 0
    }
  ],
  "root": "tests/fixtures"
}
```

**结论**：通过（警告走 stderr，程序没有中断）

---

## 8. 异常：没建索引直接 search，退出码 1

**命令**

```powershell
Remove-Item index.json
python minisearch.py search docs python
echo "exit=$LASTEXITCODE"
```

**期望**：提示先跑 `index`，退出码 1，不抛异常堆栈

**实际输出**

```
请先运行 index 建立索引
exit=1
```

**结论**：通过

---

## 9. 跨目录：换个工作目录也能搜到（D2 互评指出后加的）

D2 在 `review.md` 里提过：在 `docs/` 子目录里执行 `python ../minisearch.py search ../docs/ python`
会报「请先运行 index 建立索引」。我们确认属实（原来 `index.json` 是按当前工作目录找的），
改成按脚本目录找之后补了这一条测试。

**命令**（先 `cd` 到别处，故意不在项目目录里）

```powershell
cd C:\
python D:\D1\groups\26级-D1\minisearch.py search docs python
echo "exit=$LASTEXITCODE"
```

**期望**：正常命中，且输出里的路径仍是相对形式 `docs/notes.txt: 2`

**实际输出**

```
docs/notes.txt: 2
  python 处理文件
docs/scope.md: 1
  - 一个目录（可以有任意层子目录），例如 `python minisearch.py index docs`
exit=0
```

**结论**：通过。`ask.py` 同理（`HERE = Path(__file__).resolve().parent`），
在 `docs/` 里跑 `python ..\ask.py ask "典型使用场景是什么？" --offline` 也能取到 `docs/scope.md:8`。

---

## 补充：验收会顺手抽查的两条

**参数错误退出码 2**（`argparse` 自动处理）

```powershell
python minisearch.py
```

```
usage: minisearch [-h] {index,search} ...
minisearch: error: the following arguments are required: command
exit=2
```

**两次索引逐字节一致**

```powershell
python minisearch.py index docs
Get-FileHash index.json
python minisearch.py index docs
Get-FileHash index.json     # 两次 Hash 必须相同
```

```
索引 4 个文件 → index.json
索引 4 个文件 → index.json
```

本组实测：两次 `index.json` 的 SHA256 都是
`352EC4C952AD0B10681745353790294BF4FEBEAFF6E1A6E7E6A86B4800DE85DD`，
完全一致；跑完 `git status --short` 没有改动。

**`--json` 能被程序解析（W2 补件）**

```powershell
python minisearch.py index docs --json
python minisearch.py search docs python --json
```

```
{
  "command": "index",
  "root": "docs",
  "index": "index.json",
  "files": 4
}
```

```
{
  "command": "search",
  "root": "docs",
  "keyword": "python",
  "count": 2,
  "hits": [
    {
      "path": "docs/notes.txt",
      "count": 2,
      "line": "python 处理文件"
    },
    {
      "path": "docs/scope.md",
      "count": 1,
      "line": "- 一个目录（可以有任意层子目录），例如 `python minisearch.py index docs`"
    }
  ]
}
```

**结论**：通过。`--json` 时 stdout 只有这一个 JSON 对象，人看的提示和警告都走 stderr；
退出码与文本模式一致（有命中 0、没命中 1、参数错 2），所以脚本只管读 stdout 就够。

**中文 `top_words` 按单字统计（W2 补件）**

```powershell
python minisearch.py index docs --top 5
Get-Content index.json -Raw
```

`index.json` 里 `guide/intro.md` 的片段：

```json
{
  "chars": 29,
  "lines": 2,
  "path": "guide/intro.md",
  "top_words": [
    ["minisearch", 1],
    ["一", 1],
    ["个", 1],
    ["你", 1],
    ["入", 1]
  ],
  "words": 4
}
```

**结论**：通过。英文/数字按词、中文按单字计数；`words` 仍是「按空白切分的词数」（这里是 4），
和 `top_words` 的口径不同，两处都写进了 `README` 与 `scope.md` 的已知限制。

---

## 跑完记得复位

第 6、7、8 条会把 `index.json` 换成空目录或 `tests/fixtures` 的版本，甚至删掉。全部测完、提交之前，回到 `docs` 上重跑一次，让随仓库提交的 `index.json` 是正式那一份：

```powershell
python minisearch.py index docs
git status --short
```
