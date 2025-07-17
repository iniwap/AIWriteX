import json

from .llm_client import AIForgeLLMClient
from .executor import AIForgeExecutor
from rich.console import Console


def should_use_detailed_prompt(instruction: str) -> bool:
    """判断是否使用详细的用户指令模式"""
    if not instruction:
        return False

    instruction_lower = instruction.lower()

    # 1. 长度判断 - 超过200字符通常是详细指令
    if len(instruction) > 200:
        return True

    # 2. 技术实现关键词 - 包含具体技术实现细节
    technical_keywords = [
        # 代码结构相关
        "函数",
        "function",
        "def ",
        "class ",
        "方法",
        "method",
        "返回格式",
        "return format",
        "数据格式",
        "data format",
        "严格遵守",
        "strictly follow",
        "必须",
        "must",
        # Web抓取相关
        "css选择器",
        "css selector",
        "xpath",
        "beautifulsoup",
        "requests",
        "urllib",
        "html",
        "dom",
        "meta标签",
        "meta tag",
        "time标签",
        "time tag",
        # 数据处理相关
        "json",
        "xml",
        "csv",
        "pandas",
        "numpy",
        "并行",
        "parallel",
        "concurrent",
        "threadpool",
        "异步",
        "async",
        "await",
        # 搜索引擎相关
        "百度",
        "baidu",
        "bing",
        "360",
        "搜狗",
        "sogou",
        "搜索引擎",
        "search engine",
        "爬虫",
        "crawler",
        # 配置和格式相关
        "配置",
        "config",
        "参数",
        "parameter",
        "param",
        "模板",
        "template",
        "格式化",
        "format",
    ]

    # 3. 代码块标识 - 包含代码块或代码示例
    code_indicators = [
        "```",
        "`",
        "import ",
        "from ",
        "def ",
        "class ",
        "if __name__",
        "__result__",
        "print(",
        "return ",
    ]

    # 4. 详细规范关键词 - 包含详细的规范说明
    specification_keywords = [
        "按优先级",
        "priority",
        "依次尝试",
        "try in order",
        "遵从以下策略",
        "follow strategy",
        "处理逻辑",
        "processing logic",
        "停止条件",
        "stop condition",
        "终止条件",
        "termination condition",
        "至少",
        "at least",
        "不少于",
        "no less than",
        "过滤掉",
        "filter out",
        "排序",
        "sort",
        "优先",
        "priority",
    ]

    # 5. 多步骤指令 - 包含多个步骤的复杂任务
    multi_step_keywords = [
        "第一步",
        "step 1",
        "首先",
        "first",
        "然后",
        "then",
        "接下来",
        "next",
        "最后",
        "finally",
        "步骤",
        "step",
        "流程",
        "process",
        "顺序",
        "sequence",
        "依次",
        "in order",
    ]

    # 检查各类关键词
    keyword_groups = [
        technical_keywords,
        code_indicators,
        specification_keywords,
        multi_step_keywords,
    ]

    # 如果在多个关键词组中都找到匹配，说明是详细指令
    matched_groups = 0
    for keywords in keyword_groups:
        if any(keyword in instruction_lower for keyword in keywords):
            matched_groups += 1

    # 匹配2个或以上关键词组，认为是详细指令
    if matched_groups >= 2:
        return True

    # 6. 特殊模式检测 - 包含特定的详细指令模式
    detailed_patterns = [
        # 包含具体的URL模式
        r"https?://[^\s]+",
        # 包含CSS选择器模式
        r'["\'][.#][^"\']+["\']',
        # 包含代码变量模式
        r"\{[^}]+\}",
        # 包含函数调用模式
        r"\w+\([^)]*\)",
    ]

    import re

    for pattern in detailed_patterns:
        if re.search(pattern, instruction):
            return True

    return False


def get_aiforge_system_prompt(user_prompt=None):
    base_prompt = """
# 角色定义
你是 CodeForge，一个专业的 Python 代码生成和执行助手。

# 代码生成规则
- 生成的代码必须能在标准 Python 环境中直接执行
- 使用已预装的库：requests, BeautifulSoup, pandas, numpy 等
- 将最终结果赋值给 __result__ 变量
- 确保代码具有适当的错误处理

# 执行环境
- Python 解释器已预装常用库
- 可以访问网络进行数据获取
- 支持文件读写操作
"""

    if user_prompt and should_use_detailed_prompt(user_prompt):
        # 详细指令时，基本 prompt 作为背景
        return f"{base_prompt}\n\n# 用户详细指令\n请严格按照以下用户指令执行：\n{user_prompt}"
    else:
        # 简单指令时，基本 prompt 提供更多指导
        return (
            f"{base_prompt}\n\n# 任务要求\n{user_prompt or '请根据用户指令生成相应的 Python 代码'}"
        )


class AIForgeTask:
    def __init__(self, llm_client: AIForgeLLMClient, max_rounds):
        self.client = llm_client
        self.executor = AIForgeExecutor()
        self.console = Console()
        self.instruction = None
        self.system_prompt = None
        self.max_rounds = max_rounds

    def run(self, instruction: str = None, system_prompt: str = None):
        """执行AI代码生成任务"""
        if instruction:
            self.instruction = instruction
        if system_prompt:
            self.system_prompt = system_prompt

        # 动态构建 system prompt
        if not system_prompt:
            system_prompt = get_aiforge_system_prompt(self.instruction)

        if not self.instruction:
            self.console.print("[red]没有提供指令[/red]")
            return None

        # 从配置中获取最大轮数
        max_rounds = getattr(self, "max_rounds", 5)

        self.console.print(
            f"[yellow]开始处理任务指令，最大尝试轮数{max_rounds}[/yellow]",
            style="bold",
        )

        rounds = 1
        while rounds <= max_rounds:
            self.console.print(f"\n[cyan]===== 第 {rounds} 轮执行 =====[/cyan]")

            # 生成代码
            self.console.print("🤖 正在生成代码...", style="dim white")
            response = self.client.generate_code(self.instruction, self.system_prompt)

            if not response:
                self.console.print(f"[red]第 {rounds} 轮：LLM 未返回响应[/red]")
                rounds += 1
                continue

            # 提取代码块
            code_blocks = self.executor.extract_code_blocks(response)
            if not code_blocks:
                self.console.print(f"[yellow]第 {rounds} 轮：未找到可执行的代码块[/yellow]")
                rounds += 1
                continue

            self.console.print(f"📝 找到 {len(code_blocks)} 个代码块")

            # 执行代码块
            success = False
            for i, code in enumerate(code_blocks):
                if code.strip():
                    self.console.print(
                        f"⚡ 开始执行代码块 {i+1}/{len(code_blocks)}...", style="dim white"
                    )

                    # 显示代码
                    # self.console.print(f"[dim]\n{code}[/dim]")

                    result = self.executor.execute_python_code(code)

                    # 详细打印执行结果
                    if result["success"]:
                        self.console.print(f"✅ 代码块 {i+1} 执行成功", style="green")

                        # 打印具体的执行结果
                        if result.get("result"):
                            result_content = result["result"]
                            try:
                                result_json = json.dumps(
                                    result_content, ensure_ascii=False, indent=2
                                )
                                self.console.print(f"📋 执行结果:\n{result_json}")
                            except Exception as e:
                                self.console.print(f"📋 输出执行结果出错：{str(e)}")

                            # 如果获取到有效结果，标记成功
                            if isinstance(result_content, dict) and result_content.get("results"):
                                success = True
                        else:
                            self.console.print("⚠️ 没有返回结果")

                    else:
                        self.console.print(
                            f"❌ 代码块 {i+1} 执行失败: {result.get('error', '未知错误')}",
                            style="red",
                        )

            # 如果本轮成功，退出循环
            if success:
                self.console.print(f"🎉 第 {rounds} 轮执行成功，任务完成！", style="bold green")
                break
            else:
                self.console.print(f"⚠️ 第 {rounds} 轮执行未获得有效结果", style="yellow")

            rounds += 1

        # 打印最终总结
        if rounds > max_rounds:
            self.console.print(f"❌ 已达到最大轮数 {max_rounds}，任务未完成", style="bold red")

        self.console.print("\n📊 执行总结:")
        self.console.print(f"  - 总轮数: {rounds - 1}/{max_rounds}")
        self.console.print(f"  - 历史记录: {len(self.executor.history)} 条")
        self.console.print(f"  - 任务状态: {'完成' if success else '未完成'}")

        return self.executor.history

    def done(self):
        """任务完成清理"""
        pass


class AIForgeManager:
    """AIForge任务管理器"""

    def __init__(self, llm_manager, max_rounds):
        self.llm_manager = llm_manager
        self.tasks = []
        self.max_rounds = max_rounds

    def new_task(self, instruction: str = None, client: AIForgeLLMClient = None) -> AIForgeTask:
        """创建新任务"""
        if not client:
            client = self.llm_manager.get_client()

        task = AIForgeTask(client, self.max_rounds)
        if instruction:
            task.instruction = instruction
        self.tasks.append(task)
        return task
