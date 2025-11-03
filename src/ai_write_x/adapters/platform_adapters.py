from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.ai_write_x.config.config import Config
from src.ai_write_x.tools.wx_publisher import pub2wx
from src.ai_write_x.core.base_framework import ContentResult
from src.ai_write_x.utils import utils


class PlatformType(Enum):
    """统一的平台类型定义"""

    WECHAT = "wechat"
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    TOUTIAO = "toutiao"
    BAIJIAHAO = "baijiahao"
    ZHIHU = "zhihu"
    DOUBAN = "douban"

    @classmethod
    def _get_display_names(cls):
        """获取显示名称映射字典"""
        return {
            "wechat": "微信公众号",
            "xiaohongshu": "小红书",
            "douyin": "抖音",
            "toutiao": "今日头条",
            "baijiahao": "百家号",
            "zhihu": "知乎",
            "douban": "豆瓣",
        }

    @classmethod
    def get_all_platforms(cls):
        """获取所有支持的平台"""
        return [platform.value for platform in cls]

    @classmethod
    def get_display_name(cls, platform_value: str) -> str:
        """获取平台的显示名称"""
        return cls._get_display_names().get(platform_value, platform_value)

    @classmethod
    def get_platform_key(cls, display_name: str) -> str:
        """根据显示名称获取平台键"""
        for key, name in cls._get_display_names().items():
            if name == display_name:
                return key
        return "wechat"

    @classmethod
    def get_all_display_names(cls) -> list:
        """获取所有平台的显示名称列表"""
        display_names = cls._get_display_names()
        return [display_names[p.value] for p in cls]

    @classmethod
    def is_valid_platform(cls, platform_name: str) -> bool:
        """验证平台名称是否有效"""
        return platform_name in cls.get_all_platforms()


@dataclass
class PublishResult:
    success: bool
    message: str
    platform_id: Optional[str] = None
    error_code: Optional[str] = None


class PlatformAdapter(ABC):
    """平台适配器基类"""

    @abstractmethod
    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化内容"""
        pass

    @abstractmethod
    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """发布内容"""
        pass

    def supports_html(self) -> bool:
        """是否支持HTML格式"""
        return False

    def supports_template(self) -> bool:
        """是否支持模板功能"""
        return False

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.__class__.__name__.replace("Adapter", "").lower()


class WeChatAdapter(PlatformAdapter):
    """微信公众号适配器"""

    def supports_html(self) -> bool:
        """是否支持HTML格式"""
        return True

    def supports_template(self) -> bool:
        """是否支持模板功能"""
        return True

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为微信公众号HTML格式"""
        config = Config.get_instance()

        if content_result.content_format == "html":
            return content_result.content
        else:
            fmt = config.article_format.lower()

            # 格式化发布
            if config.format_publish:
                content = content_result.content
                if fmt == "markdown":
                    content = f"# {content_result.title}\n\n{content_result.content}"
                elif fmt == "text":
                    content = f"{content_result.title}\n\n{content_result.content}"

                return utils.get_format_article(f".{fmt}", content)
            else:
                return content_result.content

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """发布到微信公众号"""

        config = Config.get_instance()
        # 获取所有有效的微信凭据
        valid_credentials = [
            cred
            for cred in config.wechat_credentials
            if cred.get("appid") and cred.get("appsecret")
        ]

        # 冗余检查
        if not valid_credentials:
            return PublishResult(
                success=False,
                message="未找到有效的微信公众号凭据，请在配置中填写 appid 和 appsecret",
                platform_id=PlatformType.WECHAT.value,
                error_code="MISSING_CREDENTIALS",
            )

        # 循环向所有账号发布
        publish_results = []
        success_count = 0
        # 微信不支持markdown，需要生成简单的html
        content = self.format_content(content_result)
        for credential in valid_credentials:
            appid = credential["appid"]
            appsecret = credential["appsecret"]
            author = credential.get("author", "")

            try:
                result, _, success = pub2wx(
                    content_result.title,
                    content_result.summary,
                    content,
                    appid,
                    appsecret,
                    author,
                    cover_path=kwargs.get("cover_path", None),
                )
                publish_results.append(
                    {"appid": appid, "author": author, "success": success, "message": result}
                )

                if success:
                    success_count += 1

            except Exception as e:
                publish_results.append(
                    {
                        "appid": appid,
                        "author": author,
                        "success": False,
                        "message": f"发布异常: {str(e)}",
                    }
                )

        # 生成汇总结果
        total_count = len(valid_credentials)
        overall_success = success_count > 0

        if success_count == total_count:
            summary_message = f"成功发布到所有 {total_count} 个微信公众号"
        elif success_count > 0:
            summary_message = f"部分发布成功：{success_count}/{total_count} 个账号发布成功"
            # 添加失败详情
            failed_accounts = [r for r in publish_results if not r["success"]]
            if failed_accounts:
                summary_message += "\n失败账号："
                for failed in failed_accounts:
                    summary_message += (
                        f"\n- {failed['author']}({failed['appid'][-4:]}): {failed['message']}"
                    )
        else:
            summary_message = f"发布失败：所有 {total_count} 个账号都发布失败"
            # 添加所有失败详情
            for failed in publish_results:
                summary_message += (
                    f"\n- {failed['author']}({failed['appid'][-4:]}): {failed['message']}"
                )

        return PublishResult(
            success=overall_success,
            message=summary_message,
            platform_id=PlatformType.WECHAT.value,
            error_code=None if overall_success else "PARTIAL_OR_TOTAL_FAILURE",
        )


class XiaohongshuAdapter(PlatformAdapter):
    """小红书适配器"""

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为小红书特有格式"""
        title = content_result.title
        content = content_result.content

        # 小红书特色：emoji、标签、分段
        formatted = f"✨ {title} ✨\n\n"

        # 添加引人注目的开头
        formatted += "🔥 今天分享一个超有用的内容！\n\n"

        # 处理正文内容，每段添加emoji
        paragraphs = content.split("\n\n")
        emoji_list = ["💡", "🌟", "✨", "🎯", "💫", "🔥", "👀", "💪"]

        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip() and not paragraph.startswith("#"):
                emoji = emoji_list[i % len(emoji_list)]
                formatted += f"{emoji} {paragraph.strip()}\n\n"

        # 添加互动引导
        formatted += "💬 你们觉得呢？评论区聊聊～\n\n"

        # 添加相关标签
        formatted += "#AI写作 #内容创作 #自媒体运营 #干货分享 #效率工具 #科技前沿"

        return formatted

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """小红书发布（待开发）"""
        return PublishResult(
            success=False,
            message="小红书发布功能待开发 - 需要接入小红书开放平台API",
            platform_id=PlatformType.XIAOHONGSHU.value,
            error_code="NOT_IMPLEMENTED",
        )


class DouyinAdapter(PlatformAdapter):
    """抖音适配器"""

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为短视频脚本格式"""
        title = content_result.title
        content = content_result.content

        script = f"🎬 【视频脚本】{title}\n\n"

        # 开场白
        script += "【开场】（3秒）\n"
        script += "大家好！今天我们来聊一个超有意思的话题...\n\n"

        # 将内容分解为短视频脚本段落（适合60秒短视频）
        paragraphs = [
            p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("#")
        ][:3]

        for i, paragraph in enumerate(paragraphs, 1):
            script += f"【第{i}部分】（15-20秒）\n"
            # 简化段落内容，适合口语化表达
            simplified = paragraph[:100] + "..." if len(paragraph) > 100 else paragraph
            script += f"{simplified}\n\n"

        # 结尾引导
        script += "【结尾】（5秒）\n"
        script += "如果觉得有用，记得点赞关注哦！我们下期见～\n\n"

        # 添加标签建议
        script += "📝 建议标签：#知识分享 #干货 #学习 #科技"

        return script

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """抖音发布（待开发）"""
        return PublishResult(
            success=False,
            message="抖音发布功能待开发 - 需要接入抖音开放平台API",
            platform_id=PlatformType.DOUYIN.value,
            error_code="NOT_IMPLEMENTED",
        )


class ToutiaoAdapter(PlatformAdapter):
    """今日头条适配器"""

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为今日头条格式"""
        title = content_result.title
        content = content_result.content
        summary = content_result.summary

        # 今日头条偏好清晰的结构和较长的标题
        formatted = f"# {title}\n\n"

        # 添加导读
        formatted += f"**📖 导读**\n\n{summary}\n\n"
        formatted += "---\n\n"

        # 处理正文内容，添加小标题结构
        paragraphs = [
            p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("#")
        ]

        section_titles = ["核心观点", "深度分析", "实践应用", "未来展望", "总结思考"]

        for i, paragraph in enumerate(paragraphs):
            # 每隔几段添加小标题
            if i > 0 and i % 2 == 0 and i // 2 < len(section_titles):
                formatted += f"## 🎯 {section_titles[i // 2]}\n\n"

            formatted += f"{paragraph}\n\n"

        # 添加结尾互动
        formatted += "---\n\n"
        formatted += "**💭 你的看法**\n\n"
        formatted += (
            "对于这个话题，你有什么不同的见解？欢迎在评论区分享你的观点，让我们一起讨论！\n\n"
        )
        formatted += "*如果觉得内容有价值，请点赞支持一下～*"

        return formatted

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """今日头条发布（待开发）"""
        return PublishResult(
            success=False,
            message="今日头条发布功能待开发 - 需要接入头条号开放平台API",
            platform_id=PlatformType.TOUTIAO.value,
            error_code="NOT_IMPLEMENTED",
        )


class BaijiahaoAdapter(PlatformAdapter):
    """百家号适配器"""

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为百家号格式"""
        title = content_result.title
        content = content_result.content
        summary = content_result.summary

        # 百家号注重原创性和专业性
        formatted = f"# {title}\n\n"

        # 添加原创声明
        formatted += "**📝 原创声明**\n\n"
        formatted += (
            "*本文为原创内容，未经授权禁止转载。如需转载请联系作者获得授权并注明出处。*\n\n"
        )
        formatted += "---\n\n"

        # 处理正文，添加专业化结构
        paragraphs = [
            p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("#")
        ]

        # 添加目录（如果内容较长）
        if len(paragraphs) > 4:
            formatted += "**📋 本文目录**\n\n"
            for i in range(min(5, len(paragraphs))):
                formatted += f"{i+1}. 核心要点分析\n"
            formatted += "\n---\n\n"

        # 分段处理，每3段添加小标题
        section_count = 1
        for i, paragraph in enumerate(paragraphs):
            if i > 0 and i % 3 == 0:
                formatted += f"## 📊 {section_count}. 深度解析\n\n"
                section_count += 1

            formatted += f"{paragraph}\n\n"
        # 添加专业结尾
        formatted += "---\n\n"
        formatted += "**🎯 总结**\n\n"

        # 生成总结段落
        if summary:
            formatted += f"{summary}\n\n"
        else:
            # 从内容中提取关键点作为总结
            key_points = self._extract_key_points(paragraphs)
            formatted += (
                f"通过以上分析，我们可以看出{key_points}。这些观点为我们提供了新的思考角度。\n\n"
            )

        # 添加专业版权声明
        formatted += "---\n\n"
        formatted += "**📄 版权声明**\n\n"
        formatted += (
            "*本文观点仅代表作者个人立场，不代表平台观点。如有不同见解，欢迎理性讨论。*\n\n"
        )
        formatted += "*原创不易，如果本文对您有帮助，请点赞支持。转载请联系作者授权。*"

        return formatted

    def _extract_key_points(self, paragraphs: list) -> str:
        """从段落中提取关键点"""
        if not paragraphs:
            return "相关话题具有重要意义"

        # 简单的关键点提取逻辑
        first_paragraph = paragraphs[0] if paragraphs else ""
        if len(first_paragraph) > 50:
            return first_paragraph[:50] + "等核心要点"
        return "该话题的多个重要方面"

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """百家号发布（待开发）"""
        return PublishResult(
            success=False,
            message="百家号发布功能待开发 - 需要接入百度百家号API",
            platform_id=PlatformType.BAIJIAHAO.value,
            error_code="NOT_IMPLEMENTED",
        )


class ZhihuAdapter(PlatformAdapter):
    """知乎适配器"""

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为知乎格式"""
        title = content_result.title
        content = content_result.content
        summary = content_result.summary

        # 知乎偏好问答式和深度分析
        formatted = f"# {title}\n\n"

        # 添加TL;DR摘要
        formatted += f"**TL;DR：** {summary}\n\n"
        formatted += "---\n\n"

        # 处理正文，添加逻辑结构
        paragraphs = [
            p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("#")
        ]

        # 添加目录结构（如果内容较长）
        if len(paragraphs) > 3:
            formatted += "**📚 本文目录：**\n\n"
            section_titles = ["核心观点", "深度分析", "实践应用", "总结思考"]
            for i in range(min(len(section_titles), len(paragraphs))):
                formatted += f"- {section_titles[i]}\n"
            formatted += "\n---\n\n"

        # 分段处理，添加逻辑标题
        section_titles = ["🎯 核心观点", "🔍 深度分析", "💡 实践应用", "🤔 总结思考"]

        for i, paragraph in enumerate(paragraphs):
            # 根据位置添加合适的小标题
            if i < len(section_titles):
                formatted += f"## {section_titles[i]}\n\n"
            elif i > 0 and i % 2 == 0:
                formatted += "## 📖 进一步思考\n\n"

            formatted += f"{paragraph}\n\n"

        # 添加知乎特色的互动引导
        formatted += "---\n\n"
        formatted += "**💬 讨论时间**\n\n"
        formatted += "你怎么看这个问题？欢迎在评论区分享你的想法和经验，我们一起深入讨论！\n\n"
        formatted += "*觉得有价值的话，请点赞支持一下，让更多人看到这个内容～*\n\n"
        formatted += "**🔔 关注我，获取更多深度内容分析**"

        return formatted

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """知乎发布（待开发）"""
        return PublishResult(
            success=False,
            message="知乎发布功能待开发 - 需要接入知乎API或使用浏览器自动化",
            platform_id=PlatformType.ZHIHU.value,
            error_code="NOT_IMPLEMENTED",
        )


class DoubanAdapter(PlatformAdapter):
    """豆瓣适配器"""

    def format_content(self, content_result: ContentResult, **kwargs) -> str:
        """格式化为豆瓣格式"""
        title = content_result.title
        content = content_result.content

        # 豆瓣偏好文艺性和个人化表达
        formatted = f"# {title}\n\n"

        # 添加情感化开头
        formatted += "*写在前面：最近在思考这个话题，想和大家分享一些个人的感悟和思考*\n\n"
        formatted += "---\n\n"

        # 处理正文，保持文艺风格
        paragraphs = [
            p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("#")
        ]

        connectors = [
            "说到这里，",
            "想起来，",
            "不禁让我想到，",
            "或许，",
            "突然觉得，",
            "有时候想想，",
        ]

        for i, paragraph in enumerate(paragraphs):
            # 添加文艺化的连接词（除了第一段）
            if i > 0:
                import random

                connector = random.choice(connectors)
                formatted += f"{connector}"

            formatted += f"{paragraph}\n\n"

        # 添加豆瓣特色的个人化结尾
        formatted += "---\n\n"
        formatted += "*写在最后：*\n\n"
        formatted += (
            "以上只是个人的一些浅见和感悟，每个人的经历和思考都不同，所以观点也会有差异。\n\n"
        )
        formatted += "如果你也有类似的想法，或者有不同的见解，都欢迎在评论区和我交流讨论。\n\n"
        formatted += "🌟 *如果觉得有共鸣，不妨点个赞让我知道～*\n\n"
        formatted += "📚 *更多思考和分享，欢迎关注我的豆瓣*"

        return formatted

    def publish_content(self, content_result: ContentResult, **kwargs) -> PublishResult:
        """豆瓣发布（待开发）"""
        return PublishResult(
            success=False,
            message="豆瓣发布功能待开发 - 需要使用浏览器自动化工具",
            platform_id=PlatformType.DOUBAN.value,
            error_code="NOT_IMPLEMENTED",
        )
