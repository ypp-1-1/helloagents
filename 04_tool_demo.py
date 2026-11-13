"""
Hello Agents · 用 ToolExecutor 管理工具

这一节不调用大模型，只验证「工具执行器」本身能不能用：
    注册工具 → 列出工具 → 按名字取出函数 → 传参执行 → 拿到 Observation

注意文件名：ToolExecutor 那个模块必须叫 tool_executor.py。
Python 的模块名不能以数字开头（03ToolExecutor.py 会报 SyntaxError），
所以章节号只能放在注释和 README 里，不能放在文件名开头。
"""

from tool_executor import ToolExecutor


# --- 工具本体：这里先用 Mock 数据，换成 SerpApi 只需改函数体 ---
MOCK_SEARCH_DB = [
    (
        ["geforce", "显卡", "rtx", "消费"],
        "【NVIDIA 官网】GeForce RTX 50 系列（Blackwell 架构，2026-01 发布）\n"
        "型号：RTX 5090 / RTX 5080 / RTX 5070 Ti / RTX 5070\n"
        "显存：RTX 5090 为 32GB GDDR7\n"
        "起售价：RTX 5070 549 美元起\n"
        "来源：nvidia.com/geforce",
    ),
    (
        ["数据中心", "ai", "b200", "gb300", "算力", "训练"],
        "【NVIDIA 新闻室】Blackwell Ultra（GB300）已量产出货（2026-08）\n"
        "定位：面向大模型训练/推理的数据中心 GPU\n"
        "单柜 72 颗 GPU，HBM3e 容量较 B200 提升 1.5 倍\n"
        "来源：nvidianews.nvidia.com",
    ),
    (
        ["最新", "英伟达", "nvidia", "gpu", "gpu型号"],
        "【NVIDIA 官网】截至 2026-11，最新产品线：\n"
        "消费级：GeForce RTX 50 系列（Blackwell），旗舰 RTX 5090\n"
        "数据中心：Blackwell Ultra（GB300）\n"
        "来源：nvidia.com",
    ),
]


def search(query: str) -> str:
    """模拟网页搜索。真实场景换成 SerpApi / Tavily 的 HTTP 调用。"""
    q = query.lower()
    hits = []
    for keywords, text in MOCK_SEARCH_DB:
        score = sum(1 for k in keywords if k in q)
        if score:
            hits.append((score, text))

    if not hits:
        return f"没有检索到与「{query}」相关的结果（离线 Mock 数据）。"

    hits.sort(key=lambda item: -item[0])
    return "\n\n---\n\n".join(text for _, text in hits[:2])


if __name__ == "__main__":
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册搜索工具
    search_description = (
        "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    )
    toolExecutor.registerTool("Search", search_description, search)

    # 3. 打印可用工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 模拟智能体的一次 Action 调用
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误:未找到名为 '{tool_name}' 的工具。")

    # 5. 反面用例：取一个不存在的工具，getTool 应该返回 None 而不是崩掉
    print("\n--- 反面用例: 调用不存在的工具 Calculator ---")
    missing = toolExecutor.getTool("Calculator")
    if missing is None:
        print("✅ getTool 返回 None，说明未注册的工具被正确拦住了。")
    else:
        print("❌ 不应该取到函数")
