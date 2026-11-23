# review.md — 交叉互评（D1 评 D2）

- 组别：**D1**（陆奕然 / 胡轩也 / 李福程）
- 互评对象：**D2**（倪生浩 / 李科学 / 史智轩）
- 代码来源：`https://github.com/Nishenghao/XiW/tree/w2-d2/groups/26级-D2`，分支 `w2-d2`，head `48d8519`（用 `git ls-remote` 核对过）。下面每条都标了文件行号，可以直接对着看，不是凭印象写的。
- 状态：**已完成**。W2 交的时候这一节只写了「未取得 D2 仓库地址」，这一版把两条都补上了。

---

## 一、我们给 D2 的意见

### 意见一（做得好的）：`top_words` 的取词口径从一开始就是对的

`groups/26级-D2/minisearch.py:43`：

```python
text = re.findall(r'[a-zA-Z]+', context.lower()) + re.findall(r'[\u4e00-\u9fa5]', context)
```

英文按连续字母切、中文按单字切，`top_words` 直接就是任务书要的形态：中文两个字「索引」不会整段算成一个词。

这正是我们 W2 被打回的点。我们一开始写的是 `text.lower().split()`，`index.json` 里出现过 `"是一个迷你全文检索工具。"` 这种整句当词的条目，返工之后才改成一样的口径。这一条我们不如他们。

另外两处他们做得比我们早：

- `minisearch.py:38-40` 兜了 `PermissionError`，我们只兜了 `UnicodeDecodeError`；
- `minisearch.py:7` 的 `INDEX_PATH = Path(__file__).resolve().parent / "index.json"`——`index.json` 按脚本目录定位，换个工作目录也能跑。他们给我们的第一条意见提的正是这个要求，他们先在自己代码里做到了。

### 意见二（问题，影响验收）：`index.json` 的 `root` 存的是绝对路径，别人 clone 下来必然搜不到，而且不报错

`groups/26级-D2/minisearch.py:65`：

```python
index = {"root": root.resolve().as_posix(), "files": files}
```

`root.resolve()` 把 `docs` 变成了绝对路径。于是提交进仓库的 `index.json` 长这样：

```json
"root": "C:/Users/NiShh/Desktop/XiW/groups/26级-D2/docs"
```

**他们自己的 README 写的是相对路径。** `groups/26级-D2/README.md:20-22` 的字段示例是：

```json
{
  "root": "docs",
  "files": [
```

代码和文档各说一套：照着 README 写代码的人会以为里面是 `docs`，实际拿到的是作者本机的绝对路径。

**后果一：任何人 clone 下来直接 `search`，一定搜不到，而且退出码是 0。**

`search()` 拼路径用的是 `file_path = root / record["path"]`（`minisearch.py:91`），这个绝对路径在别人机器上不存在，`open` 抛 `OSError`，被 `except OSError: continue` 吞掉（`:95-96`）；所有文件都被 `continue` 掉之后 `results` 为空，程序走到 `print(f'没有找到 "{keyword}"')`（`:113-115`）就 `return` 了。

用户看到的是「这个词不存在」，不是「索引路径不对」；脚本拿到的退出码还是 0，没法靠它判断是搜空了还是索引坏了。

我们实测过——把 `groups/26级-D2/` 原样拷到 `D:\社团\_check\d2verify`，不重新建索引：

```
$ python minisearch.py search "python"
没有找到 "python"
exit=0
```

而作者本机上同一条命令输出的是 `.../docs/sub/b.txt: 3` 和 `.../docs/a.md: 1`。

**同一份仓库、同一条命令，结果是「两条命中」还是「搜不到」，只取决于你在谁的电脑上跑。**

**后果二：输出的路径格式不符合任务书。** 重新 `index` 之后能搜到了，但打印出来是：

```
D:/社团/_check/d2verify/docs/sub/b.txt: 3
  第1行: python
```

任务书要求的是 `docs/guide/intro.md: 3` 这种相对路径 + 缩进匹配行。绝对路径又长又暴露本机用户名——`NiShh` 现在明晃晃地出现在提交进仓库的 `index.json` 里，以及 `tests.md` 第 40、49、56 行贴的输出里。

**建议**：`root` 存成 `docs`，读取时按脚本目录补全，显示时用记录里的相对串：

```python
root = Path(index["root"])
if not root.is_absolute():
    root = INDEX_PATH.parent / root
...
print(f"{record['path']}: {count}")
```

### 附带三条（不影响主要结论，供参考）

1. **`--json` 只做了一半**：`index` 子命令有 `--json`（`minisearch.py:130`），`search` 没有——`:132-133` 只注册了 `keyword` 一个参数。W2 补件要求「补 `--json`」是为了让别的程序读结果，`search` 这边更该有。

2. **README 的函数签名和代码对不上**：`README.md:37-39` 写的是

   ```python
   def iter_files(root: Path)                    -> list[Path]
   def analyze_file(root: Path, file_path: Path) -> dict
   def build_index(root: Path, paths: list[Path])-> None
   ```

   实际代码是 `analyze_file(root, top, file_path)`（`minisearch.py:29`）、`build_index(root, top, js, paths)`（`:56`），而且 `iter_files` 返回的是 `list[str]`（`:24` 里已经 `as_posix()` 转过了），不是 `list[Path]`。README 是他们唯一的接口文档，签名错了别人没法照着接。

3. **`index` 没有 `--out`，跑一次别的目录就把正式索引冲掉**：`build_index` 无条件写 `INDEX_PATH`（`minisearch.py:66`）。我们实测，在已有 `index.json` 的目录里执行 `python minisearch.py index tmp_empty`，`index.json` 立刻被换成 `{"root": ".../tmp_empty", "files": []}`，原来的索引没了。他们 `tests.md` 第 2 条（空目录测试）就会踩到这个问题。加个 `--out`，或者「目标目录没有可索引文件时不覆盖已有索引」，都能避免。

---

## 二、D2 给我们的两条（原文照抄，不改写）

摘自 `groups/26级-D2/review.md`：

> **bug**
> *   **现象**：跨目录执行 `search` 命令时，程序崩溃或提示找不到索引文件。
> *   **复现命令**：
>     1. 在根目录执行：`python minisearch.py index docs/`
>     2. 进入子目录：`cd docs`
>     3. 在子目录执行搜索：`python ../minisearch.py search ../docs/ python`
> *   **期望 vs 实际**：
>     *   期望：应该能正常搜出结果。
>     *   实际：报错提示“请先运行 index 建立索引”或抛出路径异常。

> **使用问题**
> *   **现象**：无法检索到子目录中的文件（如 `docs/guide/intro.md` 搜不到）。
> *   **建议**：`indexer.py` 第 13 行使用了 `base.glob("*")`，这只会遍历当前层，不会进入子文件夹。建议改成 `base.rglob("*")` 或 `base.glob("**/*")` 以支持递归遍历。

### 我们对第 1 条的处理：属实，已修

我们的 `index.json` 原来是按「当前工作目录」找的（`open("index.json")`），在 `docs/` 里执行确实会报「请先运行 index 建立索引」。这一版改成固定按脚本目录找：

- `minisearch.py`：新增 `INDEX_PATH = Path(__file__).resolve().parent / "index.json"`，读和写都用它；
- `searcher.search(index, keyword, base=None)` 新增 `base` 参数，显示路径仍是 `docs/xxx.md`；
- `ask.py` 用 `HERE = Path(__file__).resolve().parent` 定位 `index.json` 和 `docs/`。

实测：在 `groups/26级-D1/docs/`、在 `C:\` 下分别执行
`python D:\D1\groups\26级-D1\minisearch.py search docs python`，都正常输出

```
docs/notes.txt: 2
  python 处理文件
docs/scope.md: 1
  - 一个目录（可以有任意层子目录），例如 `python minisearch.py index docs`
```

### 我们对第 2 条的处理：和代码对不上，判断是看了更早的版本

我们 `indexer.py` 第 13 行是 `def iter_files(root):`，真正遍历在第 18 行：

```python
for path in sorted(base.rglob("*")):
```

**从一开始就是 `rglob`**，不是 `base.glob("*")`。`tests.md` 第 3 条（`docs/guide/intro.md` 在子目录里）
和第 1 条（`docs/` 下 4 个文件含 `guide/intro.md`）都能证明确实递归了。
所以这条不需要改；如果他们在某个 commit 上看到过 `glob`，欢迎把 sha 发我们，我们照着复查。

---

## 三、自评（提 PR 前对一遍）

1. **接口先定死**：`index.json` 的七个字段在 README 里冻结，A 生产、B 消费、C 校验，三个人不需要读对方的实现。字段改了要走「群里说 → README 改 → 再改代码」。
2. **依赖单向**：`minisearch.py → indexer.py`、`minisearch.py → searcher.py`；`searcher.py` 不 import `indexer`。任何一个人换掉自己那个文件内部写法，另外两个都不用动。
3. **两次一致**：同一目录连续跑两次 `index`，`index.json` 逐字节相同，SHA256 = `352EC4C952AD0B10681745353790294BF4FEBEAFF6E1A6E7E6A86B4800DE85DD`（改了 `top_words` 口径后的新值，`tests.md` 有记录）。
4. **异常不吞**：非 UTF-8 文件跳过 + stderr 警告 + 退出码仍为 0；目录不存在退出码 1；参数错误退出码 2。三条都有实测记录在 `tests.md`。
5. **能在任意目录跑**：这是 D2 指出后修的，`minisearch.py`、`ask.py` 都按脚本目录定位 `index.json` 和 `docs/`，不用先 `cd`。
6. **三个人的 commit 都在 PR 里**：A 的 `indexer.py`、B 的 `searcher.py`/`minisearch.py`、C 的目录与文档，作者分别显示为 `Hxy070627-NUIST`、`liguchengniubi`、`LuYiRan42`。

## 四、我们踩过、写下来提醒自己的坑

- 网页上传文件很容易传错分支或传错目录（我们有过一次把 `indexer.py` 传到 `main` 根目录），**改代码走本地 git，别用网页上传**。
- 分支要基于 `w2-d1` 起，不是基于 `main`、也不是基于别人的个人分支，否则文件会落在仓库根目录。
- `tests.md` 里的实际输出必须从终端整段复制，手打的输出验收现场一跑就露馅。
- 索引里存绝对路径这种错，自己机器上永远测不出来——必须把整个目录复制到别处跑一次。这次就是 D2 提醒才发现我们自己的 `index.json` 也有同类问题（按 CWD 找）。
