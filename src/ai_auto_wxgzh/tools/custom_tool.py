import os
import glob
import random
import sys
from typing import List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from rich.console import Console
from aipyapp.aipy.taskmgr import TaskManager

from src.ai_auto_wxgzh.tools.wx_publisher import pub2wx
from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.config.config import Config
from src.ai_auto_wxgzh.tools.search_service import SearchService
from src.ai_auto_wxgzh.utils import log
from src.ai_auto_wxgzh.tools import search_template


class ReadTemplateToolInput(BaseModel):
    pass


# 1. Read Template Tool
class ReadTemplateTool(BaseTool):
    name: str = "read_template_tool"
    description: str = (
        "从本地读取HTML模板文件，此模板必须作为最终输出的基础结构，保持视觉风格和布局效果，仅替换内容部分"
    )
    args_schema: Type[BaseModel] = ReadTemplateToolInput

    def _run(self) -> str:
        config = Config.get_instance()

        # 获取模板文件的绝对路径
        template_dir_abs = utils.get_res_path(
            "templates",
            os.path.join(utils.get_current_dir("knowledge", False)),
        )

        random_template = True
        if config.template:  # 如果指定模板，且必须存在才能不随机
            template_filename = (
                config.template if config.template.endswith(".html") else f"{config.template}.html"
            )
            selected_template_file = os.path.join(template_dir_abs, template_filename)
            if os.path.exists(selected_template_file):  #
                random_template = False

        # 需要随机
        if random_template:
            template_dir_abs = utils.get_res_path(
                "templates",
                os.path.join(utils.get_current_dir("knowledge", False)),
            )

            template_files_abs = glob.glob(os.path.join(template_dir_abs, "*.html"))

            if not template_files_abs:
                log.print_log(
                    f"在目录 '{template_dir_abs}' 中未找到任何模板文件。如果没有模板请将config.yaml中的use_template设置为false"
                )
                # 出现这种错误无法继续，立即终止程序，防止继续消耗Tokens（不终止CrewAI可能会重试）
                sys.exit(1)

            selected_template_file = random.choice(template_files_abs)

        with open(selected_template_file, "r", encoding="utf-8") as file:
            selected_template_content = file.read()

        template_content = utils.compress_html(
            selected_template_content,
            config.use_compress,
        )  # 压缩html，降低token消耗

        return f"""
        【HTML模板 - 必须作为最终输出的基础】
        {template_content}

        【模板使用指南】
        1. 上面是完整的HTML模板，您必须基于此模板进行内容适配
        2. 必须保持的元素：
        - 所有<section>标签的布局结构和内联样式
        - 原有的视觉层次、色彩方案和排版风格
        - 卡片式布局、圆角和阴影效果
        - SVG动画元素和交互特性
        3. 内容适配规则：
        - 标题替换标题、段落替换段落、列表替换列表
        - 当新内容比原模板内容长或短时，合理调整，不破坏布局
        - 保持原有的强调部分（粗体、斜体、高亮等）应用于新内容的相应部分
        - 保持图片位置不变
        4. 严格禁止：
        - 不添加新的style标签或外部CSS
        - 不改变原有的色彩方案（限制在三种色系内）
        - 不修改模板的整体视觉效果和布局结构
        5. 最终输出必须是基于此模板的HTML，保持相同的视觉效果和样式，但内容已更新

        【重要提示】
        您的任务是将前置任务生成的文章内容适配到此模板中，而不是创建新的HTML。
        请分析模板结构，识别内容区域，然后将新内容填充到对应位置。
        """


# 2. Publisher Tool
# - 考虑到纯本地函数执行，采用回调形式
# - 降低token消耗，降低AI出错率
class PublisherTool:
    def run(self, content, appid, appsecret, author):
        try:
            content = utils.decompress_html(content)  # 固定格式化HTML
        except Exception as e:
            log.print_log(f"解压html出错：{str(e)}")

        # 提取审核报告中修改后的文章
        article = utils.extract_modified_article(content)
        msg_type = "status"
        title, digest = None, None
        # 提取标题和摘要
        try:
            title, digest = utils.extract_html(article)
        except Exception as e:
            log.print_log(f"从文章中提取标题、摘要信息出错: {e}", msg_type)
            return

        if title is None:
            result = "无法提取文章标题，请检查文章是否成功生成？"
        else:
            # 发布到微信公众号
            if Config.get_instance().auto_publish:
                # 自动发布，不保存最终文章
                result, _, _ = pub2wx(title, digest, article, appid, appsecret, author)
            else:
                # 非自动保存需要保存最终文章，以便后续发布
                msg_type = "info"
                result = "文章生成完成，请手动发布（点击上方发布菜单按钮）。"
                dir_path = utils.mkdir(utils.get_article_dir())
                with open(
                    os.path.join(dir_path, f"{utils.sanitize_filename(title)}.html"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(article)

        log.print_log(result, msg_type)


# 3. AIPy Search Tool
class AIPySearchToolInput(BaseModel):
    """输入参数模型"""

    topic: str = Field(..., description="要搜索的话题")
    urls: List[str] = Field(default=[], description="参考文章链接数组")
    reference_ratio: float = Field(..., description="参考文章借鉴比例")


class AIPySearchTool(BaseTool):
    """AIPy搜索工具"""

    name: str = "aipy_search_tool"
    description: str = "搜索关于特定主题的最新信息、数据和趋势。"

    args_schema: type[BaseModel] = AIPySearchToolInput

    def _run(self, topic: str, urls: List[str], reference_ratio: float) -> str:
        """执行AIPy搜索"""
        results = None
        config = Config.get_instance()
        original_cwd = os.getcwd()

        if len(urls) == 0:
            log.print_log("开始执行搜索，请耐心等待...")
            if config.use_search_service:
                results = self._use_search_service(
                    topic, config.aipy_search_max_results, config.aipy_search_min_results
                )
            else:
                results = self._nouse_search_service(
                    topic, config.aipy_search_max_results, config.aipy_search_min_results
                )
            source_type = "搜索"
        else:
            log.print_log("开始提取参考链接中的文章信息，请耐心等待...")
            extract_results = search_template.extract_urls_content(urls, topic)
            # 这里只要参考文章获取到一条有效结果，就认为通过， 当然也可以len(urls)条结果
            if search_template.validate_search_result(
                extract_results, min_results=1, search_type="reference_article"
            ):
                results = extract_results.get("results")

            source_type = "参考文章"

        os.chdir(original_cwd)

        return self._formatted_result(topic, urls, reference_ratio, source_type, results)

    def _formatted_result(self, topic, urls, reference_ratio, source_type, results):
        if results:
            # 根据模式过滤掉相应字段为空的条目
            filtered_results = []
            for result in results:
                title = result.get("title", "").strip()

                # 根据模式判断不同的内容字段
                if len(urls) > 0:
                    # 借鉴模式：检查content字段
                    content_field = result.get("content", "").strip()
                else:
                    # 搜索模式：检查abstract字段
                    content_field = result.get("abstract", "").strip()

                # 如果标题和对应的内容字段都不为空，则保留该条目
                if title and content_field:
                    filtered_results.append(result)

            if filtered_results:
                if len(urls) > 0:
                    formatted = (
                        f"关于'{topic}'的{source_type}结果（参考比例：{reference_ratio}）：\n\n"
                    )
                else:
                    formatted = f"关于'{topic}'的{source_type}结果：\n\n"

                for i, result in enumerate(filtered_results, 1):
                    formatted += f"## 结果 {i}\n"
                    formatted += f"**标题**: {result.get('title', '无标题')}\n"
                    formatted += f"**发布时间**: {result.get('pub_time', '未知时间')}\n"
                    formatted += f"**摘要**: {result.get('abstract', '无摘要')}\n"
                    # 如果是URL提取，添加更多内容信息
                    if len(urls) > 0 and "content" in result:
                        formatted += f"**内容**: {result.get('content', '')}...\n"
                    formatted += "\n"
                return formatted
            else:
                return f"未能找到关于'{topic}'的有效{source_type}结果。"
        else:
            return f"未能找到关于'{topic}'的{source_type}结果。"

    def _use_search_service(self, topic, max_results, min_results):
        try:
            # 执行搜索
            return SearchService().aipy_search(topic, max_results, min_results)
        except Exception as e:
            log.print_traceback("搜索过程中发生错误：", e)
            return None

    def _nouse_search_service(self, topic, max_results, min_results):
        try:
            # 第一步：尝试使用本地模板代码
            template_result = search_template.search_web(topic, max_results, min_results)
            if template_result:
                return template_result.get("results")

            # 第二步：渐进式AI生成
            console = Console()
            console.print("[yellow]本地模板搜索失败，尝试基于模板的约束性生成搜索代码...[/yellow]")
            task_manager = TaskManager(Config.get_instance().get_aipy_settings(), console=console)

            # 先尝试基于模板的约束性生成
            constrained_result = self._try_template_guided_ai(
                topic, max_results, min_results, task_manager
            )
            if search_template.validate_search_result(constrained_result, min_results, "ai_guided"):
                return constrained_result.get("results")

            console.print("[yellow]基于模板的约束性生成搜索失败，尝试完全自由的AI生成...[/yellow]")
            # 最后尝试完全自由的AI生成
            free_result = self._try_free_form_ai(topic, max_results, min_results, task_manager)
            if search_template.validate_search_result(free_result, min_results, "ai_free"):
                return free_result.get("results")

            return None

        except Exception as e:
            log.print_traceback("搜索过程中发生错误：", e)
            return None

    def _try_template_guided_ai(self, topic, max_results, min_results, task_manager):
        """基于模板模式的约束性AI生成"""
        search_instruction = search_template.get_template_guided_search_instruction(
            topic, max_results, min_results
        )

        task = None
        try:
            task = task_manager.new_task(search_instruction)
            task.run()

            # 反向遍历历史记录，只验证摘要和日期
            for entry in reversed(task.runner.history):
                result = entry.get("result", {}).get("__result__")
                if search_template.simple_validate_search_result(result, min_results, "ai_guided"):
                    return result
            return None
        finally:
            if task:
                task.done()

    def _try_free_form_ai(self, topic, max_results, min_results, task_manager):
        """完全自由的AI生成"""
        search_instruction = search_template.get_free_form_ai_search_instruction(
            topic, max_results, min_results
        )

        task = None
        try:
            task = task_manager.new_task(search_instruction)
            task.run()

            # 反向遍历历史记录，只验证摘要和日期
            for entry in reversed(task.runner.history):
                result = entry.get("result", {}).get("__result__")
                if search_template.simple_validate_search_result(result, min_results, "ai_free"):
                    return result
            return None
        finally:
            if task:
                task.done()
