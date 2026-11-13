# Hello Agents 练习

跟《Hello Agents》教程手写的代码，边看边实现。

## 文件

| 文件 | 内容 |
| --- | --- |
| `01.py` | `HelloAgentsLLM`：兼容 OpenAI 接口的流式客户端 |
| `02_react_agent.py` | ReAct 智能体（Mock 工具版）：Thought → Action → Observation 循环 |
| `tool_executor.py` | `ToolExecutor`：工具注册 / 查找 / 描述生成（第 3 节） |
| `04_tool_demo.py` | 用 `ToolExecutor` 注册并执行搜索工具（第 4 节） |

> `tool_executor.py` 这个名字不能改回 `03ToolExecutor.py`：Python 的模块名不能以数字开头，
> 否则 `import` 会直接报 `SyntaxError`。章节号只能放在注释或 README 里。

## 运行

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install openai python-dotenv

cp .env.example .env            # 然后填入自己的 key
python 02_react_agent.py
python 04_tool_demo.py
```

## 说明

`02_react_agent.py` 里的 `Search` 工具返回的是写死的假数据，不需要注册任何搜索 API。
换成真实搜索时只改 `search()` 函数体，ReAct 循环代码不用动。

`.env` 已在 `.gitignore` 中，不会被提交。
