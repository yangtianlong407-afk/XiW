"""W3 最小闭环：检索 -> 拼 Prompt -> 调 LLM -> 回答 + 出处。

只依赖 index.json（W2 的产物）和三个环境变量：
    LLM_API_KEY   必填
    LLM_BASE_URL  选填，默认 https://api.deepseek.com
    LLM_MODEL     选填，默认 deepseek-chat

用法：
    python ask.py ask "社团什么时候招新？"
    python ask.py ask "社团什么时候招新？" --json
    python ask.py ask "社团什么时候招新？" --offline   # 不联网，只打印将要发送的 Prompt
"""

import argparse
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# 脚本所在目录：index.json 和 docs/ 都相对它来找，从哪个目录调用都能跑
HERE = Path(__file__).resolve().parent

SYSTEM_PROMPT = """你是一个只根据资料回答问题的助手。三条硬规则：
1. 只根据下面给出的资料回答，不许用你自己的知识补充；
2. 每个结论后面标出处，格式为 file:line，例如 docs/招新.md:12；
3. 资料里没有答案时，只回答「文档里没有」，不许编造。"""

# 中文两字组合里出现这些词就不算关键词，避免「什么」「怎么」把无关行捞出来
STOP_GRAMS = {"什么", "怎么", "如何", "为什", "哪些", "哪个", "是否", "可以", "请问", "一下", "我们", "他们"}

# 「没装 requests」这条提示只打一次，重试时不重复刷屏
_WARNED_URLLIB = False


class ApiError(Exception):
    """调用模型时的可读错误，打印信息而不是抛 traceback。"""


def load_index(path=None):
    index_path = Path(path) if path else HERE / "index.json"
    if not index_path.exists():
        print("缺少 index.json，请先运行：python minisearch.py index docs/", file=sys.stderr)
        return None
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"index.json 读取失败：{exc}", file=sys.stderr)
        return None


def keywords(question):
    """把问题拆成英文词 + 中文两字组合，给检索用。"""
    low = question.lower()
    words = re.findall(r"[a-z0-9_]{2,}", low)
    cjk = re.sub(r"[^\u4e00-\u9fff]", "", low)
    grams = [cjk[i:i + 2] for i in range(len(cjk) - 1)]
    grams = [g for g in grams if g not in STOP_GRAMS]

    out, seen = [], set()
    for token in words + grams:
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


def find_passages(index, question, top_k=3):
    """回到源文件取命中行，返回 [(路径, 行号, 原文)]。"""
    keys = keywords(question)
    if not keys:
        return []
    shown_root = str(index.get("root", "docs")).rstrip("/\\")
    root = Path(shown_root)
    if not root.is_absolute():
        root = HERE / root            # index 里存的是相对路径，按脚本所在目录解析
    ranked = []
    for item in index.get("files", []):
        path = root / item["path"]
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue                      # 读不了的文件跳过，不影响整次检索
        for no, line in enumerate(lines, start=1):
            low = line.lower()
            hits = sum(1 for k in keys if k in low)
            if hits:
                shown = f"{shown_root}/{item['path']}"
                ranked.append((hits, shown, no, line.strip()))
    ranked.sort(key=lambda r: (-r[0], r[1], r[2]))
    return [(path, no, text) for _, path, no, text in ranked[:top_k]]


def build_messages(question, passages):
    material = "\n\n".join(f"[{i}] {path}:{no}\n{text}" for i, (path, no, text) in enumerate(passages, start=1))
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"资料：\n{material}\n\n问题：{question}"},
    ]


def _post_json(url, headers, body, timeout):
    """发一次 HTTP POST。有 requests 就用 requests，没有就退回标准库 urllib。"""
    try:
        import requests
    except ImportError:
        requests = None

    if requests is not None:
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        except requests.exceptions.Timeout:
            raise TimeoutError("请求超时")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("连不上服务器")
        try:
            return resp.status_code, resp.json()
        except ValueError:
            return resp.status_code, {}

    global _WARNED_URLLIB
    if not _WARNED_URLLIB:
        print("提示：没装 requests，本次用标准库 urllib；建议 pip install -r requirements.txt", file=sys.stderr)
        _WARNED_URLLIB = True
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {}
        return exc.code, payload
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise TimeoutError("请求超时")
        raise ConnectionError("连不上服务器")
    except socket.timeout:
        raise TimeoutError("请求超时")


def call_llm(messages, timeout=30):
    """发一次请求；超时、连接失败、5xx 各重试一次。"""
    key = os.environ.get("LLM_API_KEY", "").strip()
    if not key:
        print("缺少 LLM_API_KEY。设置方法：", file=sys.stderr)
        print('  PowerShell:  $env:LLM_API_KEY="你的key"', file=sys.stderr)
        print("  CMD:         set LLM_API_KEY=你的key", file=sys.stderr)
        print("  （key 不要写进代码，也不要提交进仓库）", file=sys.stderr)
        raise ApiError("")

    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
    model = os.environ.get("LLM_MODEL", "deepseek-chat").strip()

    # 环境变量里混进中文时（最常见：把文档里的「你的key」占位符原样粘进来），
    # HTTP 头按 latin-1 编码会直接抛 UnicodeEncodeError，报错完全看不懂。这里先挡掉。
    for label, value in (("LLM_API_KEY", key), ("LLM_BASE_URL", base), ("LLM_MODEL", model)):
        if not value.isascii():
            shown = value if len(value) <= 12 else value[:12] + "…"
            print(f"环境变量 {label} 里有非 ASCII 字符，请求发不出去。", file=sys.stderr)
            print("  最常见的原因是照抄了文档里的占位符（比如「你的key」），或者多粘了中文说明。", file=sys.stderr)
            print(f"  当前值：{shown}", file=sys.stderr)
            print("  请换成服务商给的真实值，例如：", file=sys.stderr)
            print('    $env:LLM_API_KEY="sk-xxxxxxxxxxxxxxxx"', file=sys.stderr)
            raise ApiError("")

    url = f"{base}/chat/completions"
    body = {"model": model, "messages": messages, "temperature": 0}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    last_error = None
    for attempt in range(2):
        try:
            status, data = _post_json(url, headers, body, timeout)
        except TimeoutError:
            last_error = "请求超时（30 秒）"
        except ConnectionError:
            last_error = "连不上服务器，检查网络或 LLM_BASE_URL"
        else:
            if status == 401:
                raise ApiError("401：key 无效或已过期，检查 LLM_API_KEY")
            if status == 429:
                raise ApiError("429：请求太频繁，等一会儿再试")
            if 500 <= status < 600:
                last_error = f"{status}：服务端错误"
            elif status != 200:
                raise ApiError(f"{status}：{json.dumps(data, ensure_ascii=False)[:200]}")
            else:
                return data
        if attempt == 0:
            time.sleep(1)
    raise ApiError(f"重试后仍失败：{last_error}")


def output(question, answer, sources, latency, tokens, as_json):
    payload = {
        "question": question,
        "answer": answer,
        "sources": sources,
        "latency": round(latency, 2),
        "tokens": tokens,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(answer)
    if sources:
        print()
        print("来源：" + "、".join(sources))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ask")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ask = sub.add_parser("ask", help="问一个问题")
    p_ask.add_argument("question")
    p_ask.add_argument("--json", action="store_true", help="输出 JSON")
    p_ask.add_argument("--top-k", type=int, default=3, help="取前几条资料，默认 3")
    p_ask.add_argument("--index", default=None, help="索引文件路径，默认用脚本目录下的 index.json")
    p_ask.add_argument("--offline", action="store_true", help="不联网，只打印 Prompt（调试用）")

    args = parser.parse_args(argv)

    index = load_index(args.index)
    if index is None:
        return 1

    passages = find_passages(index, args.question, args.top_k)
    if not passages:
        # 没有命中就直接拒答，不浪费一次 API 调用
        output(args.question, "文档里没有", [], 0.0, None, args.json)
        return 0

    messages = build_messages(args.question, passages)
    sources = [f"{path}:{no}" for path, no, _ in passages]

    if args.offline:
        print("=== 将要发送的 Prompt（--offline，不联网）===")
        print(messages[1]["content"])
        print("\n=== 来源 ===")
        print("、".join(sources))
        return 0

    started = time.perf_counter()
    try:
        data = call_llm(messages)
    except ApiError as exc:
        if str(exc):
            print(str(exc), file=sys.stderr)
        return 1
    latency = time.perf_counter() - started

    try:
        answer = (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError):
        print(f"返回格式看不懂：{json.dumps(data, ensure_ascii=False)[:300]}", file=sys.stderr)
        return 1

    if not answer:
        print("模型返回了空内容，请重试或换一个模型", file=sys.stderr)
        return 1

    usage = data.get("usage") or {}
    tokens = {"prompt": usage.get("prompt_tokens"), "completion": usage.get("completion_tokens")}
    output(args.question, answer, sources, latency, tokens, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())

