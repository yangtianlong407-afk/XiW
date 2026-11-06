# tests.md — 8 条测试与真实输出

测试环境：Windows 11 + PowerShell，Python 3.12.14，仓库 `groups/26级-D1/`。
下面每条的「实际输出」都是**从终端整段复制**的，不是手打的。命令都在 `groups/26级-D1/` 下执行。

## 先准备素材（只做一次）

```powershell
cd D:\D1
New-Item -ItemType Directory -Path docs\guide, tests\fixtures -Force
@("# 入门", "minisearch 是一个迷你全文检索工具。") | Out-File docs\guide\intro.md -Encoding utf8
@("python 处理文件", "python 也可以写脚本来统计") | Out-File docs\notes.txt -Encoding utf8
New-Item -ItemType File tests\fixtures\empty.txt
"中文测试" | Out-File tests\fixtures\gbk.txt -Encoding oem
Get-ChildItem -Recurse docs, tests | Select-Object FullName, Length
```

`-Encoding oem` 写出来的是本机代码页（中文 Windows 上是 GBK），用来测「非 UTF-8」那一条。

---

## 1. 正常：索引一个含子目录的目录

**命令**

```powershell
python minisearch.py index docs
```

**期望**：两个文件都被收进索引，`docs/guide/intro.md` 的 `path` 是相对 `docs` 的 `guide/intro.md`

**实际输出**

```
索引 2 个文件 → index.json
```

**结论**：通过

---

## 2. 正常：同一个词出现多次，次数要对

**命令**

```powershell
python minisearch.py search docs python
```

**期望**：`notes.txt` 里 `python` 出现 2 次，第二行给出第一处匹配原文

**实际输出**

```
docs/notes.txt: 2
  python 处理文件
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
索引 2 个文件 → index.json
索引 2 个文件 → index.json
```

本组实测：两次 `index.json` 的 SHA256 都是
`8E82D3D415EFB1733A7C600DF40FE8F9BD23059FD77E753D48FF98F03F421179`，
完全一致；跑完 `git status --short` 没有改动。

---

## 跑完记得复位

第 6、7、8 条会把 `index.json` 换成空目录或 `tests/fixtures` 的版本，甚至删掉。全部测完、提交之前，回到 `docs` 上重跑一次，让随仓库提交的 `index.json` 是正式那一份：

```powershell
python minisearch.py index docs
git status --short
```
