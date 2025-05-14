from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import glob
import random
import sys
from rich.console import Console
from aipyapp.aipy.taskmgr import TaskManager
from typing import Optional

from src.ai_auto_wxgzh.tools.wx_publisher import WeixinPublisher
from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.config.config import Config


class ReadTemplateToolInput(BaseModel):
    article_file: str = Field(description="前置任务生成的的文章内容")
    template: str = Field(description="本地HTML模板")
    use_compress: str = Field(description="是否压缩模板")


# 1. Read Template Tool
class ReadTemplateTool(BaseTool):
    name: str = "read_template_tool"
    description: str = "从本地读取HTML文件"
    args_schema: Type[BaseModel] = ReadTemplateToolInput

    def _run(self, article_file: str, template: str, use_compress: bool) -> str:
        # 获取模板文件的绝对路径
        template_dir_abs = utils.get_res_path(
            "templates",
            os.path.join(utils.get_current_dir("knowledge", False)),
        )

        random_template = True
        if template:  # 如果指定模板，且必须存在才能不随机
            template_filename = template if template.endswith(".html") else f"{template}.html"
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
                print(
                    f"在目录 '{template_dir_abs}' 中未找到任何模板文件。如果没有模板请将config.yaml中的use_template设置为false"
                )
                # 出现这种错误无法继续，立即终止程序，防止继续消耗Tokens（不终止CrewAI可能会重试）
                sys.exit(1)

            selected_template_file = random.choice(template_files_abs)

        with open(selected_template_file, "r", encoding="utf-8") as file:
            selected_template_content = file.read()

        return utils.compress_html(
            selected_template_content,
            use_compress,
        )  # 压缩html，降低token消耗


class PublisherToolInput(BaseModel):
    appid: str = Field(description="微信公众号 AppID")
    appsecret: str = Field(description="微信公众号 Key")
    author: str = Field(description="微信公众号作者")
    img_api_type: str = Field(description="文生图平台方")
    img_api_key: str = Field(description="文生图平台方 Key")
    img_api_model: str = Field(description="文生图模型")


# 2. Publisher Tool
class PublisherTool(BaseTool):
    name: str = "publisher_tool"
    description: str = "从本地读取HTML文件，提取内容，保存为最终文章并发布到微信公众号。"
    args_schema: Type[BaseModel] = PublisherToolInput

    def _run(
        self,
        appid: str,
        appsecret: str,
        author: str,
        img_api_type: str,
        img_api_key: str,
        img_api_model: str,
    ) -> str:
        # 自定义工具接收上一个task数据有很大随机性，这里只能从保存的文件读取数据
        tmp_article = os.path.join(utils.get_current_dir(), "tmp_article.html")

        try:
            with open(tmp_article, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(str(e))
            return "读取tmp_article.html失败，无法发布文章！"

        try:
            content = utils.decompress_html(content)  # 因为不需要直接看生成文章源码，默认不解压了
        except Exception as e:
            print(f"解压html出错：{str(e)}")

        # 提取审核报告中修改后的文章
        article = utils.extract_modified_article(content)

        # 发布到微信公众号
        result, article = self.pub2wx(
            article,
            appid,
            appsecret,
            author,
            img_api_type,
            img_api_key,
            img_api_model,
        )
        # 保存为 final_article.html
        final_article = os.path.join(utils.get_current_dir(), "final_article.html")
        with open(final_article, "w", encoding="utf-8") as f:
            f.write(article)

        return result

    def pub2wx(
        self,
        article,
        appid,
        appsecret,
        author,
        img_api_type,
        img_api_key,
        img_api_model,
    ):
        try:
            title, digest = utils.extract_html(article)
        except Exception as e:
            return f"从文章中提取标题、摘要信息出错: {e}", article
        if title is None:
            return "无法提取文章标题，请检查文章是否成功生成？", article

        publisher = WeixinPublisher(
            appid, appsecret, author, img_api_type, img_api_key, img_api_model
        )

        image_url = publisher.generate_img(
            "主题：" + title.split("|")[-1] + "，内容：" + digest,
            "900*384",
        )

        if image_url is None:
            print("生成图片出错，使用默认图片")

        # 封面图片
        media_id, _ = publisher.upload_image(image_url)
        if media_id is None:
            return "上传封面图片出错，无法发布文章", article

        # 这里需要将文章中的图片url替换为上传到微信返回的图片url
        try:
            image_urls = utils.extract_image_urls(article)
            for image_url in image_urls:
                local_filename = utils.download_and_save_image(
                    image_url,
                    utils.get_current_dir("image"),
                )
                if local_filename:
                    _, url = publisher.upload_image(local_filename)
                    article = article.replace(image_url, url)
        except Exception as e:
            print(f"上传配图出错，影响阅读，可继续发布文章:{e}")

        add_draft_result = publisher.add_draft(article, title, digest, media_id)
        if add_draft_result is None:
            # 添加草稿失败，不再继续执行
            return "上传草稿失败，无法发布文章", article

        publish_result = publisher.publish(
            add_draft_result.publishId
        )  # 可以利用返回值，做重试等处理
        if publish_result is None:
            return "发布草稿失败，无法继续发布文章", article

        article_url = publisher.poll_article_url(publish_result.publishId)
        if article_url is not None:
            # 该接口需要认证，将文章添加到菜单中去，用户可以通过菜单“最新文章”获取到
            _ = publisher.create_menu(article_url)
        else:
            print("无法获取到文章URL")  # 这里无所谓，不影响后面

        # 只有下面执行成功，文章才会显示到公众号列表，否则只能通过后台复制链接分享访问
        # 通过群发使得文章显示到公众号列表 ——> 该接口需要认证
        media_id = publisher.media_uploadnews(article, title, digest, media_id)
        if media_id is None:
            return "上传图文素材失败，无法显示到公众号文章列表", article

        sndall_ret = publisher.message_mass_sendall(media_id)
        if sndall_ret is None:
            return "无法将文章群发给用户，无法显示到公众号文章列表", article

        return "成功发布文章到微信公众号", article


# 3. AIPy Search Tool
class AIPySearchToolInput(BaseModel):
    """输入参数模型"""

    topic: str = Field(..., description="要搜索的话题")
    max_results: Optional[int] = Field(10, description="返回的最大结果数量")


class AIPySearchTool(BaseTool):
    """AIPy搜索工具"""

    name: str = "aipy_search_tool"
    description: str = "使用AIPy搜索最新的信息、数据和趋势"
    args_schema: type[BaseModel] = AIPySearchToolInput

    def _run(self, topic: str, max_results: int = 10) -> str:
        """执行AIPy搜索"""
        # 保存当前工作目录
        original_cwd = os.getcwd()
        try:
            # 初始化AIPy
            console = Console()
            # 创建TaskManager
            try:
                task_manager = TaskManager(Config.get_instance().get_aipy_config(), console=console)
            except Exception as e:
                console.print_exception()
                raise e

            # 创建搜索任务
            # 考虑到墙的因素，不要优先使用谷歌搜索
            # 微信需要无代理，所以为了整个执行成功，建议关闭
            search_instruction = f"""
            搜索关于{topic}的最新信息，包括
            1. 最新数据和统计数字
            2. 最近的事件和时间点
            3. 当前趋势和发展
            4. 权威来源的观点和分析

            搜索方法优先级（不使用需要API密钥的方式）：
            1. 使用DuckDuckGo搜索引擎，添加时间筛选参数
            2. 使用百度搜索，添加时间筛选参数
            3. 使用bing搜索，添加时间筛选参数
            4. 直接访问相关领域的权威网站并抓取最新内容
            5. 只有在上述方法都无法获取足够信息时，才考虑使用Google搜索

            请确保：
            1. 添加时间筛选参数，优先获取最近7天内的内容
            2. 对搜索结果按发布时间从新到旧排序
            3. 提取每个结果的发布日期，仅保留最近的信息
            4. 验证信息的时效性，过滤掉旧信息

            返回结构化的搜索结果，包含来源URL、发布时间和内容摘要。
            限制结果数量为{max_results}个，按时间从新到旧排序。
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
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
