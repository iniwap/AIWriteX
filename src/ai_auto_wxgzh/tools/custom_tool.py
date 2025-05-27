import os
import glob
import random
import sys
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from rich.console import Console
from aipyapp.aipy.taskmgr import TaskManager

from src.ai_auto_wxgzh.tools.wx_publisher import WeixinPublisher
from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.config.config import Config
from src.ai_auto_wxgzh.tools.search_service import SearchService
from src.ai_auto_wxgzh.utils import log


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

        # 发布到微信公众号
        result, article = self.pub2wx(article, appid, appsecret, author)
        # 保存为 final_article.html
        final_article = os.path.join(utils.get_current_dir(), "final_article.html")
        with open(final_article, "w", encoding="utf-8") as f:
            f.write(article)

        log.print_log(result)

    def pub2wx(self, article, appid, appsecret, author):
        try:
            title, digest = utils.extract_html(article)
        except Exception as e:
            return f"从文章中提取标题、摘要信息出错: {e}", article
        if title is None:
            return "无法提取文章标题，请检查文章是否成功生成？", article

        publisher = WeixinPublisher(appid, appsecret, author)

        image_url = publisher.generate_img(
            "主题：" + title.split("|")[-1] + "，内容：" + digest,
            "900*384",
        )

        if image_url is None:
            log.print_log("生成图片出错，使用默认图片")
            # 这里使用默认的好像会出错，采用默认背景图
            image_url = utils.get_res_path("UI\\bg.png", os.path.dirname(__file__) + "/../gui/")

        # 封面图片
        media_id, _, err_msg = publisher.upload_image(image_url)
        if media_id is None:
            return f"封面{err_msg}，无法发布文章", article

        # 这里需要将文章中的图片url替换为上传到微信返回的图片url
        try:
            image_urls = utils.extract_image_urls(article)
            for image_url in image_urls:
                local_filename = utils.download_and_save_image(
                    image_url,
                    utils.get_current_dir("image"),
                )
                if local_filename:
                    _, url, _ = publisher.upload_image(local_filename)
                    article = article.replace(image_url, url)
        except Exception as e:
            log.print_log(f"上传配图出错，影响阅读，可继续发布文章:{e}")

        add_draft_result, err_msg = publisher.add_draft(article, title, digest, media_id)
        if add_draft_result is None:
            # 添加草稿失败，不再继续执行
            return f"{err_msg}，无法发布文章", article

        publish_result, err_msg = publisher.publish(add_draft_result.publishId)
        if publish_result is None:
            return f"{err_msg}，无法继续发布文章", article

        article_url = publisher.poll_article_url(publish_result.publishId)
        if article_url is not None:
            # 该接口需要认证，将文章添加到菜单中去，用户可以通过菜单“最新文章”获取到
            ret = publisher.create_menu(article_url)
            if not ret:
                log.print_log(f"{ret}（公众号未认证，发布已成功）")
        else:
            log.print_log("无法获取到文章URL，无法创建菜单（可忽略，发布已成功）")

        # 最近好像会有个消息提示，但不会显示到列表，用户可以收到文章发布的消息
        # 只有下面执行成功，文章才会显示到公众号列表，否则只能通过后台复制链接分享访问
        # 通过群发使得文章显示到公众号列表 ——> 该接口需要认证
        ret, media_id = publisher.media_uploadnews(article, title, digest, media_id)
        if media_id is None:
            return f"{ret}，无法显示到公众号文章列表（公众号未认证，发布已成功）", article

        ret = publisher.message_mass_sendall(media_id)
        if ret is not None:
            return (
                f"{ret}，无法显示到公众号文章列表（公众号未认证，发布已成功）",
                article,
            )

        return "成功发布文章到微信公众号", article


# 3. AIPy Search Tool
class AIPySearchToolInput(BaseModel):
    """输入参数模型"""

    topic: str = Field(..., description="要搜索的话题")


class AIPySearchTool(BaseTool):
    """AIPy搜索工具"""

    name: str = "aipy_search_tool"
    description: str = "使用AIPy搜索最新的信息、数据和趋势"
    args_schema: type[BaseModel] = AIPySearchToolInput

    def _run(self, topic: str) -> str:
        """执行AIPy搜索"""
        config = Config.get_instance()

        # 保存当前工作目录
        original_cwd = os.getcwd()
        if config.use_search_service:
            results = self._use_search_service(topic, config.aipy_search_max_results)
        else:
            results = self._nouse_search_service(topic, config.aipy_search_max_results)

        # 恢复原始工作目录
        os.chdir(original_cwd)

        return results

    def _use_search_service(self, topic, max_results):
        try:
            # 初始化搜索服务
            search_service = SearchService()

            # 执行搜索
            results = search_service.search(topic, max_results, use_fix_results_parallel=True)

            if results:
                return str(results)
            else:
                return f"未能找到关于'{topic}'的搜索结果。"
        except Exception as e:
            return log.print_traceback("AIPy搜索时", e)

    def _nouse_search_service(self, topic, max_results):
        try:
            # 初始化AIPy
            console = Console()
            # 创建TaskManager
            try:
                task_manager = TaskManager(
                    Config.get_instance().get_aipy_settings(), console=console
                )
            except Exception as e:
                console.print_exception()
                raise e

            # 创建搜索任务
            # 考虑到墙的因素，不要优先使用谷歌搜索
            # 微信需要无代理，所以为了整个执行成功，建议关闭
            search_instruction = f"""
            请生成一个完整的Python函数，用于执行网络搜索并返回结构化结果。

            函数要求：
            1. 函数名为search_web，接受两个参数：topic(搜索主题)和max_results(最大结果数)
            2. 实现健壮的错误处理，包括：
                - 网络连接错误处理
                - 解析错误处理
                - 超时处理
                - 编码问题处理
            3. 对于每个搜索结果，必须访问原始网页并提取以下内容：
                - 详细的内容摘要（至少100字）
                - 准确的发布时间
                - 如果无法直接找到发布时间，尝试从URL、页面内容或其他元数据推断
            4. 使用多种方法提取时间信息：
                - 检查meta标签（如article:published_time）
                - 查找页面中的时间标记（如time标签或日期格式文本）
                - 分析页面结构中可能包含日期的区域（如文章头部）
            5. 实现适当的请求间隔，避免过快发送请求被网站封禁
            6. 按照以下优先级顺序尝试各种搜索方法（不使用需要API密钥的方式）：
                a. 使用百度搜索，添加时间筛选参数
                b. 使用bing搜索，添加时间筛选参数
                c. 直接访问相关领域的权威网站并抓取最新内容
                d. 使用DuckDuckGo搜索引擎，添加时间筛选参数
                e. 只有在上述方法都无法获取足够信息时，才考虑使用Google搜索
            7. 搜索内容应包括：
                a. 关于{topic}的最新数据和统计数字
                b. 最近的事件和时间点
                c. 当前趋势和发展
                d. 权威来源的观点和分析
            8. 确保搜索结果包含：
                - 来源URL
                - 发布时间
                - 内容摘要
            9. 对结果按发布时间从新到旧排序
            10. 验证信息的时效性，过滤掉旧信息，优先获取最近7天内的内容
            11. 返回格式为字典，包含以下字段：
                - timestamp: 搜索执行时间戳
                - topic: 搜索主题
                - results: 搜索结果列表，每个结果必须包含url、title、abstract和pub_time
                - success: 布尔值，表示搜索是否成功
                - error: 如果失败，包含错误信息

            限制结果数量为{max_results}个，按时间从新到旧排序。
            只返回完整的Python代码，不要有任何解释。
            """

            task = task_manager.new_task(search_instruction)

            # 执行任务
            task.run()

            # 从任务历史中提取搜索结果
            search_results = None
            for entry in task.runner.history:
                if "__result__" in entry.get("result", {}):
                    search_results = entry["result"]["__result__"]
                    break

            # 完成任务并保存结果
            task.done()

            if search_results:
                return str(search_results)
            else:
                return f"未能找到关于'{topic}'的搜索结果。"

        except Exception as e:
            return f"搜索过程中发生错误: {str(e)}"
