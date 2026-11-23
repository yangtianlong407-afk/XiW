"""W3 一键助手：准备索引 / 跑 10 条评测 / 跑 4 条错误处理。

在 groups/26级-D1/ 目录下双击「开始.bat」运行，或手动：
    python tools/wizard.py
"""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROUP = HERE.parent
ASK = GROUP / "ask.py"
EVAL = GROUP / "eval.md"


def say(msg=""):
    print(msg, flush=True)


def line(title):
    say("\n" + "=" * 60)
    say(title)
    say("=" * 60)


def run(cmd, env=None, timeout=120):
    """跑一条命令，返回 (退出码, stdout, stderr)。"""
    full_env = os.environ.copy()
    full_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd, cwd=str(GROUP), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=full_env, timeout=timeout,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


# ---------------------------------------------------------------- 准备

def step_prepare():
    line("第 1 步：准备语料和索引")

    missing = [n for n in ("scope.md", "ask.py") if not (GROUP / n).exists()]
    if missing:
        say(f"[×] 当前目录缺文件：{'、'.join(missing)}")
        say(f"    当前目录是：{GROUP}")
        say("    请把「开始.bat」和 tools 文件夹放到 groups/26级-D1/ 里再运行。")
        return False

    docs = GROUP / "docs"
    docs.mkdir(exist_ok=True)

    # 1) 把 scope.md 复制进 docs/（eval.md 的行号是按这份文件算的）
    target = docs / "scope.md"
    shutil.copyfile(GROUP / "scope.md", target)
    say(f"[✓] 已复制 scope.md → docs/scope.md")

    # 2) 两条边界素材
    code, out, err = run([sys.executable, "tools/make_fixtures.py", "docs"])
    say(f"[{'✓' if code == 0 else '×'}] 边界素材：{out or err}")

    # 3) 重建索引：优先用组里的 minisearch
    code, out, err = run([sys.executable, "minisearch.py", "index", "docs"])
    if code == 0:
        say(f"[✓] {out}")
    else:
        say(f"[!] minisearch 建索引失败，改用 tools/make_index.py")
        code, out, err = run([sys.executable, "tools/make_index.py", "docs", "index.json"])
        say(f"[{'✓' if code == 0 else '×'}] {out or err}")

    # 4) 验题
    code, out, err = run([sys.executable, "tools/check_eval.py", "eval.md", "index.json"])
    say(out or err)
    if code != 0:
        say("[×] 有题没命中：打开 eval.md，把「未命中」那题的措辞换成文档里真有的词，再运行一次本步骤。")
        return False
    say("[✓] 10 条题的检索全部通过，可以进第 2 步")
    return True


# ---------------------------------------------------------------- 评测

def parse_eval_rows(md_text):
    rows = []
    for raw in md_text.splitlines():
        s = raw.strip()
        if not s.startswith("|") or set(s) <= set("|-: "):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"编号", "#"}:
            continue
        rows.append(cells)
    return rows


def ask_json(question, env):
    code, out, err = run([sys.executable, "ask.py", "ask", question, "--json"], env=env)
    data = None
    if out:
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = None
    return code, data, out, err


def judge(kind, expected, code, data, stderr):
    if data is None:
        return False, "程序没有输出 JSON（见 评测输出.txt）"
    answer = data.get("answer", "")
    sources = data.get("sources") or []
    if "拒答" in kind:
        return answer.strip() == "文档里没有", "拒答" if answer.strip() == "文档里没有" else "没有拒答"
    if "边界" in kind:
        return code in (0, 1), "未崩溃"
    want = re.findall(r"docs/[^\s:：|]+\.md:\d+", expected)
    if not want:
        return code == 0, "无期望出处"
    hit = all(w in sources for w in want)
    return code == 0 and hit, "出处命中" if hit else "出处没对上"


def step_eval():
    line("第 2 步：跑 10 条评测（会调用真的模型，花一点额度）")

    if not os.environ.get("LLM_API_KEY"):
        say("[×] 没有 LLM_API_KEY。先在 PowerShell 里运行：")
        say('      $env:LLM_API_KEY="你的key"')
        say("    然后用同一个窗口运行开始.bat（环境变量只在当前窗口有效）。")
        return False
    if not (GROUP / "index.json").exists():
        say("[×] 没有 index.json，先做第 1 步。")
        return False

    rows = parse_eval_rows(EVAL.read_text(encoding="utf-8"))
    say(f"[i] 共 {len(rows)} 条题，开始跑……\n")

    filled, dump = [], []
    for cells in rows:
        no, question = cells[0], cells[1]
        kind = cells[2] if len(cells) > 2 else ""
        expected = cells[3] if len(cells) > 3 else ""
        code, data, out, err = ask_json(question, None)
        ok, note = judge(kind, expected, code, data, err)
        answer = (data or {}).get("answer", "") if data else (err or out or "无输出")
        sources = (data or {}).get("sources", []) if data else []
        actual = f"{note}；{answer}".replace("|", "／")
        if sources:
            actual += "；来源 " + "、".join(sources)
        if len(actual) > 160:
            actual = actual[:160] + "…"
        mark = "通过" if ok else "不通过"
        say(f"[{mark}] {no}. {question}")
        say(f"        {actual}")
        dump.append(f"### {no}. {question}\n\n- 退出码：{code}\n- 输出：\n\n```\n{out}\n```\n\n- stderr：\n\n```\n{err}\n```\n")
        cells = cells + [""] * (6 - len(cells))
        cells[4], cells[5] = actual, mark
        filled.append("| " + " | ".join(cells[:6]) + " |")

    # 用填好的表格替换 eval.md 的表格行
    lines = EVAL.read_text(encoding="utf-8").splitlines()
    out_lines, idx = [], 0
    for s in lines:
        if s.strip().startswith("|") and not set(s.strip()) <= set("|-: ") and idx < len(filled) \
                and s.strip().split("|")[1].strip() not in {"编号", "#"}:
            out_lines.append(filled[idx])
            idx += 1
        else:
            out_lines.append(s)
    (GROUP / "eval-filled.md").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    (GROUP / "评测输出.txt").write_text("\n".join(dump), encoding="utf-8")

    passed = sum(1 for f in filled if f.rstrip().endswith("| 通过 |"))
    say(f"\n[i] 通过 {passed} / {len(filled)} 条")
    say("[✓] 已生成 eval-filled.md（表格填好的版本）和 评测输出.txt（原始输出）")
    say("    人工核对一遍：能答题的答案是不是真对，别只看出处。")
    return True


# ---------------------------------------------------------------- 错误处理

def start_mock(port):
    proc = subprocess.Popen([sys.executable, str(GROUP / "tools" / "mock_llm.py"), str(port)],
                            cwd=str(GROUP), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return proc
        except OSError:
            time.sleep(0.1)
    return proc


def step_errors():
    line("第 3 步：四条错误处理（不需要 key）")

    env_no_key = {k: v for k, v in os.environ.items() if k != "LLM_API_KEY"}
    q = "典型使用场景是什么？"
    records = []

    # 1) 不设 key
    code, out, err = run([sys.executable, "ask.py", "ask", q], env=env_no_key)
    records.append(("不设 key", code, out, err))
    say(f"[{'✓' if code == 1 else '×'}] 不设 key → 退出码 {code}")

    # 2) 没有 index.json
    backup = GROUP / "index.json.bak"
    if (GROUP / "index.json").exists():
        shutil.move(str(GROUP / "index.json"), str(backup))
    try:
        code, out, err = run([sys.executable, "ask.py", "ask", q], env=env_no_key)
    finally:
        if backup.exists():
            shutil.move(str(backup), str(GROUP / "index.json"))
    records.append(("没有 index.json", code, out, err))
    say(f"[{'✓' if code == 1 else '×'}] 没有 index.json → 退出码 {code}")

    # 3) 连不上服务器
    env_bad = {"LLM_API_KEY": "test", "LLM_BASE_URL": "http://127.0.0.1:1"}
    code, out, err = run([sys.executable, "ask.py", "ask", q], env=env_bad)
    records.append(("连不上服务器", code, out, err))
    say(f"[{'✓' if code == 1 else '×'}] 连不上服务器 → 退出码 {code}")

    # 4) 模型返回空内容（本地假模型）
    mock = start_mock(8899)
    try:
        env_empty = {"LLM_API_KEY": "test", "LLM_BASE_URL": "http://127.0.0.1:8899/empty"}
        code, out, err = run([sys.executable, "ask.py", "ask", q], env=env_empty)
    finally:
        mock.terminate()
    records.append(("模型返回空内容", code, out, err))
    say(f"[{'✓' if code == 1 else '×'}] 返回空内容 → 退出码 {code}")

    blocks = ["# 错误处理记录（四条实测）", ""]
    for name, code, out, err in records:
        blocks += [f"## {name}", "", f"- 退出码：{code}", "", "**stdout**", "", "```", out or "（空）", "```", "", "**stderr**", "", "```", err or "（空）", "```", ""]
    (GROUP / "错误处理记录.md").write_text("\n".join(blocks), encoding="utf-8")
    say("\n[✓] 已生成 错误处理记录.md，可直接贴进周报 / README")
    return True


# ---------------------------------------------------------------- 菜单

def main():
    say("W3 一键助手 · 26级-D1")
    say(f"当前目录：{GROUP}")
    if not ASK.exists():
        say("[×] 这里没有 ask.py，请把整个 w3-d1 包放进 groups/26级-D1/")
        return 1

    if len(sys.argv) > 1:
        choice = sys.argv[1]
        say(f"[i] 直接执行第 {choice} 项")
        if choice == "1":
            step_prepare()
        elif choice == "2":
            step_eval()
        elif choice == "3":
            step_errors()
        else:
            say("参数只能是 1 / 2 / 3")
        return 0

    say("\n1. 准备语料和索引（先跑这个）")
    say("2. 跑 10 条评测（要先配好 LLM_API_KEY）")
    say("3. 跑四条错误处理（不用 key）")
    say("4. 全都跑一遍")
    choice = input("\n请输入 1 / 2 / 3 / 4，回车确认：").strip()

    if choice == "1":
        step_prepare()
    elif choice == "2":
        step_eval()
    elif choice == "3":
        step_errors()
    elif choice == "4":
        if step_prepare():
            step_eval()
        step_errors()
    else:
        say("没选对，重新运行再选一次。")
    try:
        input("\n按回车关闭窗口……")
    except EOFError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

