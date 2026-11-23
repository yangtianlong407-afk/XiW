# W3 评测记录（D1）

> 语料 = 仓库里的 `docs/`：`guide/intro.md`、`notes.txt`、`scope.md`，加两条边界素材。
> 方法：先 `python tools/check_eval.py eval.md index.json` 验证「期望出处」能被检索到（不花钱）；
> 再配 key 逐条跑真模型，把终端输出原样贴进「实际」列。
> 判分：**答案对 + 出处对**才算通过；只对答案不出处，不算过。

## 一、评测题（10 条）

| 编号 | 问题 | 类型 | 期望答案 / 出处 | 实际 | 通过？ |
|---|---|---|---|---|---|
| 1 | 典型使用场景是什么？ | 能答 | 作业写完后查某个词在哪个文件出现、哪份文档出现最多（docs/scope.md:8） | 典型场景是：作业写完了想确认「某个词到底在哪个文件里出现过」，或者「哪份文档里出现得最多」。(docs/scope.md:8)；来源 docs/scope.md:8、docs/scope.md:25 | 通过 |
| 2 | 支持哪些文件后缀？ | 能答 | .md 和 .txt，大小写不敏感（docs/scope.md:13） | 支持的后缀为 `.md` 和 `.txt`，大小写不敏感（`.MD` 也算）。(docs/scope.md:13)；来源 docs/scope.md:13、docs/scope.md:19、docs/notes.txt:1 | 通过 |
| 3 | 中文为什么不分词？ | 能答 | 不引入 jieba 之类的分词库；top_words 里中文按单字统计、英文按词统计，words 仍按空白切分（docs/scope.md:31） | 中文不分词的原因：不引入 jieba 之类的分词库，中文按整串统计；`words` 只按空白切分（docs/scope.md:31）。此外，中文不分词导致词频统计对中文没有参考价值，只对英文/代码标识符有意义（docs/scope.md:40）。；来源 docs/scope.md:40、docs/scope.md:31 | 否 |
| 4 | 8 条测试里几条是异常场景？ | 能答 | 3 条：目录不存在、空目录/空文件、非 UTF-8（docs/scope.md:25） | 8 条测试里有 3 条是异常场景（目录不存在、空目录/空文件、非 UTF-8）。出处：docs/scope.md:25；来源 docs/scope.md:25、docs/scope.md:8 | 通过 |
| 5 | 有没有 Web 界面？ | 能答 | 不提供 Web 界面和 HTTP 接口，只有命令行（docs/scope.md:34） | 没有 Web 界面。文档明确写着「不提供 Web 界面、不提供 HTTP 接口 —— 只有命令行」（docs/scope.md:34）。；来源 docs/scope.md:34、docs/scope.md:40 | 通过 |
| 6 | 食堂几点开门？ | 该拒答 | 文档里没有（零命中，不调 API） | 文档里没有 | 通过 |
| 7 | 学校图书馆在几楼？ | 该拒答 | 文档里没有（零命中，不调 API） | 文档里没有 | 通过 |
| 8 | 社团的指导老师是谁？ | 该拒答 | 文档里没有 | 文档里没有 | 通过 |
| 9 | docs/empty.md 里写了什么？ | 边界 | 文档里没有（空文件，索引记 0 行） | 文档里没有。；来源 docs/scope.md:1、docs/scope.md:3、docs/scope.md:7 | 通过 |
| 10 | docs/gbk.txt 里写了什么？ | 边界 | 文档里没有（非 UTF-8，索引时已跳过） | 文档里没有。；来源 docs/scope.md:3、docs/scope.md:7、docs/scope.md:12 | 通过 |

> **关于第 3 题的「否」**
> 这一格是照 `评测输出.txt` 原样抄的，没有改动模型的话。它引用的是 `scope.md` 改成
> 「`top_words` 按单字统计」**之前**的原文，说明那次运行用的是旧语料（`docs/scope.md` 还没同步）。
> 现行 `docs/scope.md:31` 写的是「中文按单字统计、英文按词统计」，所以这条回答与现在的文档对不上，
> 按「答案对 + 出处对」的标准判为不通过。
>
> 修法：`git pull` 拿到最新 `docs/scope.md` 后单独重跑这一题——
> `python ask.py ask "中文为什么不分词？" --json`，
> 把输出替换掉这格，再把「否」改回「通过」。
> 其余 9 条（1、2、4、5、6、7、8、9、10）的「实际」与 `评测输出.txt` 逐字一致。

## 二、判分口径

- **能答的 5 条**：答案意思对，且出处 `file:line` 指向的行真的包含这个结论。
- **该拒答的 3 条**：必须原样回答「文档里没有」，不能出现任何编造的人名、数字。
- **边界的 2 条**：空文件不崩、坏编码不崩；答不出也要给「文档里没有」。
- 通过率 = 通过条数 / 10，写进 README 的结果一节。

## 三、跑之前的准备（只做一次）

```powershell
# 1) 语料：把 scope.md 复制一份到 docs/ 里（原样复制，不要改行，否则下面的行号会变）
Copy-Item scope.md docs\scope.md

# 2) 两条边界素材：空文件 + 非 UTF-8 文件
python tools\make_fixtures.py docs

# 3) 重建索引（用组里的 minisearch）
python minisearch.py index docs

# 4) 验题：期望出处能不能被检索到
python tools\check_eval.py eval.md index.json
```

## 四、怎么跑真模型

```powershell
$env:LLM_API_KEY="你的key"
python ask.py ask "这个工具给谁用？"
python ask.py ask "食堂几点开门？"
python ask.py ask "这个工具给谁用？" --json
```

把每条输出贴进「实际」列，再打勾。
每条的完整终端输出另存一份 `评测输出.txt` 一起提交——验收要查的是「实际列和原始输出一致」。

## 五、已知限制

- 检索是「两字组合 + 命中行数」排序，不是向量检索；换个说法可能搜不到。
- 每类资料只取前 3 行，答案跨段落时可能漏。
- 中文没有分词，短问题（少于 2 个汉字）会退化成整句匹配，容易搜不到。
- 语料只有 4 个文件，覆盖不了「社团业务问题」；下一周应把招新、FAQ、考核等文档放进 `docs/`。
