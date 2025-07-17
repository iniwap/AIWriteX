from src.ai_write_x.aiforge.task_manager import should_use_detailed_prompt

# 简单指令示例
simple_instructions = ["今天有哪些新闻", "帮我搜索一下天气", "查询股票价格", "获取最新资讯"]

# 详细指令示例
detailed_instructions = [
    "请生成一个搜索函数，使用BeautifulSoup解析HTML，返回JSON格式",
    "按优先级依次尝试百度、Bing搜索引擎，提取meta标签中的发布时间",
    "严格遵守以下数据格式：{'results': [...], 'success': True}",
    "使用concurrent.futures.ThreadPoolExecutor并行处理，过滤掉验证页面",
]

for instruction in simple_instructions:
    print(f"'{instruction}' -> {should_use_detailed_prompt(instruction)}")  # False

for instruction in detailed_instructions:
    print(f"'{instruction}' -> {should_use_detailed_prompt(instruction)}")  # True
