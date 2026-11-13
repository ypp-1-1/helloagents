"""
Hello Agents · ReAct 智能体（Mock 版）

目的：不花一分钱、不注册任何搜索 API，先把 ReAct 的循环跑通。

循环长这样：
    Thought → Action → Action Input → （外部执行工具）→ Observation → Thought → ...
    直到模型输出 Final Answer。

工具全是本地函数：
    - Search     ：返回写死的假搜索结果（模拟 SerpApi 的返回结构）
    - Calculator ：真实执行四则运算（证明"工具就是普通函数"，不一定是 API）

想接真实搜索时，只需要改 search() 函数体，循环代码一行都不用动。
"""

import os
import re
import sys
from typing import Callable, Dict

from dotenv import load_dotenv
from openai import OpenAI

# Windows 下 Git Bash / 管道输出的默认编码是 GBK，无法打印 emoji，统一切换为 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

load_dotenv()

MODEL = os.getenv("LLM_MODEL_ID")
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    timeout=60,
)


# ==========================================================================
# 一、工具层：就是几个普通函数
# ==========================================================================

MOCK_SEARCH_DB = [
    (
        ["mate", "mate80", "mate 80", "最新", "新款", "新款", "旗舰", "发布", "刚出"],
        "【华为官网】华为 Mate 80 系列正式发布（2026-10-22）\n"
        "机型：Mate 80 / Mate 80 Pro / Mate 80 Pro Max / Mate 80 RS 非凡大师\n"
        "芯片：麒麟 9030\n"
        "起售价：5499 元（Mate 80 12GB+256GB）\n"
        "亮点：HarmonyOS 6.0 首发、卫星通信 2.0、双层 OLED 屏\n"
        "来源：consumer.huawei.com/cn/news/2026-10-22",
    ),
    (
        ["pura", "影像", "拍照", "相机"],
        "【华为官网】华为 Pura 80 系列（2026-06-11 发布）\n"
        "机型：Pura 80 / Pura 80 Pro / Pura 80 Ultra\n"
        "影像：1 英寸主摄 + 可变光圈，Ultra 搭载伸缩长焦\n"
        "起售价：4699 元\n"
        "来源：consumer.huawei.com/cn/news/2026-06-11",
    ),
    (
        ["折叠", "mate x", "matex", "三折"],
        "【华为官网】华为 Mate X7 折叠屏（2026-09-05 发布）\n"
        "形态：内折，展开 7.9 英寸\n"
        "起售价：12999 元\n"
        "来源：consumer.huawei.com/cn/news/2026-09-05",
    ),
    (
        ["价格", "多少钱", "售价", "贵", "预算"],
        "【华为商城】在售机型价格区间（截至 2026-11）\n"
        "nova 系列：2499 - 3999 元\n"
        "Pura 80 系列：4699 元起\n"
        "Mate 80 系列：5499 元起\n"
        "Mate X7 折叠：12999 元起\n"
        "来源：vmall.com 华为商城",
    ),
]


def search(query: str) -> str:
    """模拟搜索 API。真实场景下这里换成 SerpApi / Tavily 的 HTTP 调用。"""
    q = query.lower()
    hits = []
    for keywords, text in MOCK_SEARCH_DB:
        score = sum(1 for k in keywords if k in q)
        if score:
            hits.append((score, text))

    if not hits:
        return (
            f"没有检索到与「{query}」相关的结果。\n"
            "（提示：当前是离线 Mock 数据，只包含华为手机相关的几条记录）"
        )

    hits.sort(key=lambda item: -item[0])
    return "\n\n---\n\n".join(text for _, text in hits[:2])


def calculator(expr: str) -> str:
    """真实可用的计算器工具，不是假的。"""
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
        return "只支持数字和 + - * / ( ) 运算，请重新输入表达式。"
    try:
        value = eval(expr, {"__builtins__": {}}, {})
        return f"{expr} = {value}"
    except Exception as e:  # noqa: BLE001
        return f"计算失败：{e}"


TOOLS: Dict[str, Dict] = {
    "Search": {
        "func": search,
        "desc": "网页搜索。输入一段查询词，返回搜索结果的标题和摘要。适合查新闻、产品发布、价格等实时信息。",
    },
    "Calculator": {
        "func": calculator,
        "desc": "计算器。输入一个四则运算表达式，如 (5499-4699)/4699*100，返回计算结果。",
    },
}


def build_tools_desc() -> str:
    return "\n".join(f"- {name}: {info['desc']}" for name, info in TOOLS.items())


def call_tool(name: str, tool_input: str) -> str:
    """根据模型给的 Action 名分发到具体函数，异常一律转成文本返回给模型。"""
    info = TOOLS.get(name.strip())
    if info is None:
        return f"错误：不存在名为「{name}」的工具，可用工具只有 {list(TOOLS)}。"
    try:
        return str(info["func"](tool_input.strip()))
    except Exception as e:  # noqa: BLE001
        return f"工具执行出错：{e}"


# ==========================================================================
# 二、提示词：把「说话格式」约束死，这是 ReAct 能跑起来的关键
# ==========================================================================

SYSTEM_PROMPT = """你是一个可以调用外部工具的智能助手。

可用工具：
{tools_desc}

请严格按以下格式思考和行动，一次只输出一个步骤：

Question: 需要回答的问题
Thought: 你的思考过程（这一步要不要用工具、用哪个）
Action: 工具名，必须是 [{tool_names}] 之一
Action Input: 传给该工具的输入

（外部系统会把工具结果以 Observation: 的形式返回给你，你可以继续 Thought/Action）
（重复若干轮后，当你有足够信息回答时，输出：）

Thought: 我现在知道最终答案了
Final Answer: 对原始问题的完整回答

硬性要求：
1. 绝对不要自己编造 Observation，Observation 只能由外部系统给出。
2. 每一轮只能输出一个 Action。
3. Final Answer 不要出现"根据搜索结果"这类过程性话术，直接给结论，并带上来源。
"""


def build_prompt(question: str, history: str) -> str:
    tools_desc = build_tools_desc()
    tool_names = ", ".join(TOOLS)
    system = SYSTEM_PROMPT.format(tools_desc=tools_desc, tool_names=tool_names)
    return (
        system
        + "\n\n开始。\n\nQuestion: "
        + question
        + "\n"
        + history
        + ("Thought:" if not history else "")
    )


# ==========================================================================
# 三、解析层：从模型输出的文本里抠出 Action / Final Answer
# ==========================================================================

ACTION_RE = re.compile(r"Action\s*[:：]\s*(.+)")
ACTION_INPUT_RE = re.compile(r"Action\s*Input\s*[:：]\s*(.+)")
FINAL_RE = re.compile(r"Final\s*Answer\s*[:：]\s*([\s\S]+)")


def parse_step(text: str):
    """返回 (final_answer, action_name, action_input)，三者中只会有一种非空。"""
    final = FINAL_RE.search(text)
    if final:
        return final.group(1).strip(), None, None

    action = ACTION_RE.search(text)
    action_input = ACTION_INPUT_RE.search(text)
    if action:
        name = action.group(1).strip().splitlines()[0].strip(" ：:`\"'")
        payload = action_input.group(1).strip().splitlines()[0].strip() if action_input else ""
        return None, name, payload
    return None, None, None


def llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        stop=["\nObservation:", "Observation:"],  # 防止模型自己往下编 Observation
    )
    return response.choices[0].message.content or ""


# ==========================================================================
# 四、主循环
# ==========================================================================

def run_react(question: str, max_steps: int = 6) -> str:
    print(f"\n{'=' * 70}\n问题：{question}\n{'=' * 70}")
    history = ""

    for step in range(1, max_steps + 1):
        prompt = build_prompt(question, history)
        raw = llm(prompt).strip()

        final, action, action_input = parse_step(raw)

        if final:
            print(f"\n--- 第 {step} 步 ---\n{raw}\n")
            print(f"{'=' * 70}\n最终答案：\n{final}\n{'=' * 70}")
            return final

        if not action:
            print(f"⚠️  第 {step} 步没有解析出 Action，也不含 Final Answer，原文如下：\n{raw}\n")
            return ""

        print(f"\n--- 第 {step} 步 ---")
        print(raw)
        print(f"🔧 执行工具 {action}({action_input!r}) ...")
        observation = call_tool(action, action_input)
        print(f"👀 Observation: {observation}")

        history += f"{raw}\nObservation: {observation}\n"

    print("⚠️  达到最大步数仍未得到 Final Answer。")
    return ""


if __name__ == "__main__":
    run_react("华为最新发布的手机是哪款？配置和价格怎么样？")
    run_react("如果我买 Mate 80，比 Pura 80 起售价贵百分之多少？")
