import re
import os
import random
import warnings
from bs4 import BeautifulSoup
import requests
import time
import sys
import shutil
import webbrowser
import markdown
from PIL import Image
import tempfile
import urllib.parse
from pathlib import Path


def copy_file(src_file, dest_file):
    mkdir(os.path.dirname(dest_file))

    # 存在不复制
    if os.path.exists(dest_file):
        return False

    try:
        shutil.copy2(src_file, dest_file)
    except Exception as e:  # noqa 841
        pass


def mkdir(path, clean=False):
    if os.path.exists(path):
        if clean:
            shutil.rmtree(path)
            os.makedirs(path)
    else:
        os.makedirs(path)

    return path


def get_is_release_ver():
    if getattr(sys, "frozen", None):
        return True
    else:
        return False


def get_res_path(file_name, basedir=""):
    if get_is_release_ver():
        return os.path.join(sys._MEIPASS, file_name)  # type: ignore

    return os.path.join(basedir, file_name)


def get_random_platform(platforms):
    """
    根据权重随机选择一个启用的平台。
    自动归一化权重,无需用户关心总和是否为1。
    """
    # 过滤出启用的平台
    enabled_platforms = [p for p in platforms if p.get("enabled", True)]

    # 如果没有启用平台,启用所有平台
    if not enabled_platforms:
        warnings.warn("没有启用的平台，将自动启用所有平台", UserWarning)
        enabled_platforms = platforms
        for p in enabled_platforms:
            p["enabled"] = True

    # 计算启用平台的权重总和
    total_weight = sum(p["weight"] for p in enabled_platforms)

    # 如果权重总和为0或负数,平均分配权重
    if total_weight <= 0:
        warnings.warn("启用平台权重总和为0，将平均分配权重", UserWarning)
        avg_weight = 1.0 / len(enabled_platforms)
        for p in enabled_platforms:
            p["weight"] = avg_weight
        total_weight = 1.0

    # 归一化处理 - 保持相对权重比例
    if abs(total_weight - 1.0) > 0.01:
        for platform in enabled_platforms:
            platform["weight"] = platform["weight"] / total_weight
        total_weight = 1.0

    # 加权随机选择
    rand = random.uniform(0, total_weight)
    cumulative_weight = 0
    for platform in enabled_platforms:
        cumulative_weight += platform["weight"]
        if rand <= cumulative_weight:
            return platform["name"]

    # 兜底返回第一个启用的平台
    return enabled_platforms[0]["name"]


def extract_html(html, max_length=64):
    title = None
    digest = None

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    h1_tag = soup.find("h1")

    # 标题优先级：<title> > <h1>
    if title_tag:
        title = " ".join(title_tag.get_text(strip=True).split())
    elif h1_tag:
        title = " ".join(h1_tag.get_text(strip=True).split())

    # 摘要
    # 提取所有文本内容，并去除多余的空格和换行符
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    if text:
        # 如果文本长度超过最大长度，则截取前max_length个字符
        if len(text) > max_length:
            digest = text[:max_length] + "..."
        else:
            digest = text

    return title, digest


def get_latest_file_os(dir_path):
    """
    使用 os 模块获取目录下最近创建/保存的文件。
    """

    files = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, f))
    ]
    if not files:
        return None  # 如果目录为空，则返回 None

    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def extract_image_urls(html_content, no_repeate=True):
    patterns = [
        r'<img[^>]*?src=["\'](.*?)["\']',  # 匹配 src
        r'<img[^>]*?srcset=["\'](.*?)["\']',  # 匹配 srcset
        r'<img[^>]*?data-(?:src|image)=["\'](.*?)["\']',  # 匹配 data-src/data-image
        r'background(?:-image)?\s*:\s*url$["\']?(.*?)["\']?$',  # 匹配 background
    ]
    urls = []
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        urls.extend(
            [url for match in matches for url in (match.split(",") if "," in match else [match])]
        )
    if no_repeate:
        return list(set(urls))
    else:
        return urls


def download_and_save_image(image_url, local_image_folder):
    """
    下载图片并保存到本地。

    Args:
        image_url (str): 图片链接。
        local_image_folder (str): 本地图片保存文件夹。

    Returns:
        str: 本地图片文件路径，如果下载失败则返回 None。
    """
    try:
        # 创建本地图片保存文件夹
        if not os.path.exists(local_image_folder):
            os.makedirs(local_image_folder)

        # 下载图片，允许重定向
        response = requests.get(image_url, stream=True, allow_redirects=True)
        response.raise_for_status()

        # 生成本地文件名
        timestamp = str(int(time.time()))
        local_filename = os.path.join(local_image_folder, f"{timestamp}.jpg")
        # 保存图片到本地
        with open(local_filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return local_filename
    except Exception:
        return None


def compress_html(content, use_compress=True):
    if use_compress:
        return content

    # 移除注释
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    # 移除换行和制表符
    content = re.sub(r"[\n\t]+", "", content)
    # 移除多余空格（保留属性分隔空格）
    content = re.sub(r"\s+", " ", content)
    # 移除=、>、<、;、: 前后的空格
    content = re.sub(r"\s*([=><;,:])\s*", r"\1", content)
    # 移除标签间空格
    content = re.sub(r">\s+<", "><", content)
    return content


def decompress_html(compressed_content, use_compress=True):
    """
    格式化 HTML 内容，处理压缩和未压缩 HTML，确保输出的内容适合网页渲染。

    参数：
        compressed_content (str): 输入的 HTML 字符串
        use_compress (bool): 是否作为压缩 HTML 处理（True）或直接返回（False）

    返回：
        str: 格式化后的 HTML 字符串
    """
    # 如果 use_compress 为 False 或内容已格式化（有换行和缩进），直接返回
    if not use_compress or re.search(r"\n\s{2,}", compressed_content):
        return compressed_content.strip()

    try:
        # 使用 lxml 解析器处理 HTML，支持不规范的 HTML
        soup = BeautifulSoup(compressed_content, "lxml")

        # 移除多余空白和注释，清理输出
        for element in soup.find_all(text=True):
            if element.strip() == "":  # type: ignore
                element.extract()  # 移除空文本节点
            elif element.strip().startswith("<!--") and element.strip().endswith("-->"):  # type: ignore # noqa 501
                element.extract()  # 移除注释

        # 判断是否为 HTML 片段（无 DOCTYPE 或 <html> 标签）
        is_fragment = not (
            compressed_content.strip().startswith("<!DOCTYPE")
            or compressed_content.strip().startswith("<html")
        )

        if is_fragment:
            # 对于片段，避免包裹 <html> 或 <body> 标签
            formatted_lines = []
            for child in soup.contents:
                if hasattr(child, "prettify"):
                    formatted_lines.append(child.prettify().strip())  # type: ignore
                else:
                    formatted_lines.append(str(child).strip())
            return "\n".join(line for line in formatted_lines if line)

        # 对于完整 HTML 文档，返回格式化输出
        return soup.prettify(formatter="minimal").strip()

    except Exception as e:  # noqa 841
        # 错误处理：解析失败时返回原始内容
        return compressed_content.strip()


def open_url(file_url):
    try:
        if file_url.startswith(("http://", "https://")):
            webbrowser.open(file_url)
        else:
            if not os.path.exists(file_url):
                return "文件不存在！"

            file_path = Path(file_url).resolve()

            if sys.platform == "win32":
                # Windows特殊处理：直接使用文件路径
                import subprocess

                subprocess.run(["start", "", str(file_path)], shell=True)
            elif sys.platform == "darwin":
                html_url = f"file://{urllib.parse.quote(str(file_path))}"
                webbrowser.open(html_url)
            else:
                html_url = file_path.as_uri()
                webbrowser.open(html_url)

        return ""
    except Exception as e:
        return str(e)


def is_valid_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except Exception as e:  # noqa 841
        return False


def sanitize_filename(filename):
    # 定义非法字符的正则表达式
    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
    # 将非法字符替换为下划线
    sanitized = re.sub(illegal_chars, "_", filename)
    # 去除首尾的空格和点号（Windows 文件名不能以点号或空格开头/结尾）
    sanitized = sanitized.strip().strip(".")
    # 如果文件名为空，设置一个默认值
    return sanitized or "default_filename"


def is_llm_supported(llm, key_name, env_vars):
    """
    检查CrewAI是否完整支持LLM配置
    排除通过显式配置工作的提供商（如openrouter）
    """
    # OpenRouter 等提供商通过显式配置工作，不依赖ENV_VARS
    if llm.lower() == "openrouter":
        return True

    if llm.lower() not in env_vars:
        return False

    # 检查是否有正确的API密钥配置
    llm_config = env_vars[llm.lower()]
    for config in llm_config:
        if config.get("key_name") == key_name.upper():
            return True

    return False


def remove_code_blocks(content):
    """
    移除所有Markdown代码块标识但保留内容
    处理以下格式：
      ```markdown 内容 ```
      ```html 内容 ```
      ```javascript 内容 ```
      ``` 内容 ```
      `内容`
    """
    # 移除多行代码块标识（带任何语言标签）
    content = re.sub(r"```\w*\s*", "", content, flags=re.IGNORECASE)

    # 移除单行内联代码块标识
    content = re.sub(r"`([^`]*)`", r"\1", content)

    # AI这里不受控，总是带字数注释，这里强行去除
    pattern = r"""
    [(\[【]            # 起始括号（全角/半角）
    \s*               # 可选空白
    (全文\s*)?        # 可选"全文"前缀
    (约|共|总计|合计)? # 量词
    \s*\d+\s*字       # 核心匹配：数字+"字"
    \s*[)\]】]        # 结束括号
    \s*$              # 确保在行末
    """
    return re.sub(pattern, "", content, flags=re.VERBOSE | re.MULTILINE).strip()


def markdown_to_plaintext(md_text):
    """提取文章文本内容"""
    # 分步处理不同标记类型
    # 1. 处理标题标记（保留标题文本）
    text = re.sub(r"^#{1,6}\s+", "", md_text, flags=re.MULTILINE)

    # 2. 处理加粗/斜体/删除线标记（保留内容）
    text = re.sub(r"(\*\*|\*|~~|__)(.*?)\1", r"\2", text)

    # 3. 处理代码块（保留代码内容）
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)

    # 4. 处理链接和图片（保留描述文字）
    text = re.sub(r"!?$(.*?)$$[^)]*$", r"\1", text)

    # 5. 处理列表符号（保留数字索引和内容）
    text = re.sub(r"^\s*([-*+]|\d+\.)\s+", r"\1 ", text, flags=re.MULTILINE)

    # 6. 处理引用块标记（保留引用内容）
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    return text.strip()


def extract_markdown_content(content):
    """从Markdown内容中提取标题和摘要"""
    lines = content.strip().split("\n")
    title = None
    digest = ""

    # 查找第一个标题（# 开头）
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # 提取前几行作为摘要，跳过标题行和空行
    content_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            content_lines.append(line)
        if len(content_lines) >= 3:  # 取前3行非标题内容
            break

    digest = " ".join(content_lines)[:100] + "..." if content_lines else "无摘要"

    return title, digest


def extract_text_content(content):
    """从文本内容中提取标题和摘要"""
    lines = content.strip().split("\n")

    # 第一行作为标题
    title = lines[0].strip() if lines else None

    # 后续几行作为摘要
    content_lines = [line.strip() for line in lines[1:] if line.strip()]
    digest = " ".join(content_lines[:3])[:100] + "..." if content_lines else "无摘要"

    return title, digest


def text_to_html(text_content):
    """将纯文本转换为HTML"""
    lines = text_content.split("\n")
    html_lines = []

    for line in lines:
        line = line.strip()
        if line:
            html_lines.append(f"<p>{line}</p>")
        else:
            html_lines.append("<br>")

    return "\n".join(html_lines)


def get_format_article(ext, article):
    """将不同格式的文章转换为HTML"""
    if ext == ".md" or ext == ".markdown":
        # 使用 markdown 库转换 Markdown 到 HTML
        md = markdown.Markdown(extensions=["extra", "codehilite"])
        return md.convert(article)
    elif ext == ".txt":
        # txt内容（已经是从markdown提取的纯文本）直接转HTML
        return text_to_html(article)
    else:
        # 不支持的格式，返回原内容
        return article


def is_local_path(url):
    """判断URL是否为本地路径"""
    # 检查是否为网络URL
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme in ("http", "https", "ftp"):
        return False

    # 检查是否为Web路由路径(以/开头但不是真实的本地绝对路径)
    if url.startswith("/images/") or url.startswith("/static/"):
        return False  # 这些是Web路径,不是本地路径

    # 检查是否为绝对路径
    if os.path.isabs(url):
        return True

    # 检查是否为相对路径
    if url.startswith("./") or url.startswith("../"):
        return True

    # 其他情况视为本地路径
    return True


def resolve_image_path(url):
    """将图片URL解析为实际文件系统路径"""
    from src.ai_write_x.utils.path_manager import PathManager

    # 如果是网络URL,直接返回
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme in ("http", "https", "ftp"):
        return url

    # 先检查Web路由路径,再检查绝对路径
    if url.startswith("/"):
        # 尝试匹配已知的静态文件路由
        if url.startswith("/images/"):
            filename = url.replace("/images/", "")
            local_path = PathManager.get_image_dir() / filename
            return str(local_path)  # 始终返回本地路径
        # 如果不是/images/,才当作Unix绝对路径处理
        elif os.path.isabs(url):
            return url

    # 如果是绝对路径(Windows: C:\, Unix: 已在上面处理)
    if os.path.isabs(url):
        return url

    # 相对路径,相对于当前工作目录
    return url


def crop_cover_image(image_path, target_size=(900, 384)):
    """
    将封面图片裁剪为指定尺寸
    先缩放至填满目标尺寸，然后居中裁剪
    """

    try:
        # 打开原图
        img = Image.open(image_path)
        original_width, original_height = img.size
        target_width, target_height = target_size

        # 计算缩放比例，确保能填满目标尺寸
        scale_x = target_width / original_width
        scale_y = target_height / original_height
        scale = max(scale_x, scale_y)  # 使用较大的缩放比例确保填满

        # 缩放图片
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        img = img.resize((new_width, new_height), Image.LANCZOS)  # type: ignore

        # 居中裁剪
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        img = img.crop((left, top, right, bottom))

        # 生成临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img.save(temp_file.name, "JPEG", quality=95)
        temp_file.close()

        return temp_file.name

    except Exception:
        return None


def fix_mac_clipboard(value):
    """处理输入框变化，修复macOS重复粘贴问题"""
    if sys.platform == "darwin" and value:  # 仅在macOS上处理
        length = len(value)
        if length > 0 and length % 2 == 0:
            half_length = length // 2
            first_half = value[:half_length]
            second_half = value[half_length:]

            # 检查是否为重复内容
            if first_half == second_half:
                # 修正为单份内容
                # self._window[key].update(first_half)
                return first_half
    return value


def get_gui_icon():
    """获取GUI窗口图标，支持跨平台和多种用途"""
    import sys
    import os
    import base64
    from pathlib import Path

    gui_dir = Path(__file__).parent.parent / "gui"

    # 创建图标资源管理器
    class IconManager:
        def __init__(self):
            self.gui_dir = gui_dir

        def get_icon_path(self, format_type="ico"):
            """获取指定格式的图标路径"""
            icon_files = {"ico": "icon.ico", "png": "icon.png", "icns": "icon.icns"}
            return get_res_path(
                os.path.join("UI", icon_files.get(format_type, "icon.ico")), str(self.gui_dir)
            )

        def get_platform_icon(self):
            """根据平台返回最适合的图标"""
            if sys.platform == "darwin":  # macOS
                # 优先PNG的Base64编码，回退到icns
                png_path = self.get_icon_path("png")
                if os.path.exists(png_path):
                    try:
                        with open(png_path, "rb") as f:
                            return base64.b64encode(f.read())
                    except Exception:
                        pass

                icns_path = self.get_icon_path("icns")
                if os.path.exists(icns_path):
                    return icns_path

            elif sys.platform == "linux":  # Linux
                png_path = self.get_icon_path("png")
                if os.path.exists(png_path):
                    return png_path

            # Windows 或回退方案
            return self.get_icon_path("ico")

    icon_manager = IconManager()
    return icon_manager.get_platform_icon()


def get_file_extension(article_format: str) -> str:
    """根据文章格式获取文件扩展名"""
    format_map = {"HTML": "html", "MARKDOWN": "md", "TXT": "txt", "MD": "md"}

    return format_map.get(article_format.upper(), "txt")


def format_log_message(msg: str, msg_type: str = "info") -> str:
    """
    统一日志格式化接口，检测并避免重复格式化

    Args:
        msg: 原始消息
        msg_type: 消息类型

    Returns:
        格式化后的消息
    """
    # 检测是否已经包含时间戳格式 [HH:MM:SS]
    timestamp_pattern = r"^\[\d{2}:\d{2}:\d{2}\]"
    if re.match(timestamp_pattern, msg.strip()):
        return msg  # 已经格式化，直接返回

    # 检测是否已经包含消息类型格式 [TYPE]:
    type_pattern = r"\[([A-Z]+)\]:"
    if re.search(type_pattern, msg):
        # 如果只有类型没有时间戳，添加时间戳
        if not re.match(timestamp_pattern, msg.strip()):
            timestamp = time.strftime("%H:%M:%S")
            return f"[{timestamp}] {msg}"
        return msg

    # 完全未格式化，添加完整格式
    timestamp = time.strftime("%H:%M:%S")
    return f"[{timestamp}] [{msg_type.upper()}]: {msg}"
