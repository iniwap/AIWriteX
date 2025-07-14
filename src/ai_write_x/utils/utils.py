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
from urllib.parse import urlparse
import glob
import markdown
from PIL import Image
import tempfile


from src.ai_write_x.utils import log


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
        return os.path.join(sys._MEIPASS, file_name)

    return os.path.join(basedir, file_name)


def get_article_dir():
    return os.path.join(get_current_dir(), "output/article")


def get_current_dir(dir_name="", need_create_dir=True):
    current_dir = ""
    if get_is_release_ver():
        exe_path = sys.executable
        install_dir = os.path.dirname(exe_path)
        current_dir = os.path.join(os.path.normpath(install_dir), dir_name)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        current_dir = os.path.join(current_dir, "../../../", dir_name)

    # 不为空时创建目录，为空说明只是获取根目录路径
    if dir_name != "" and need_create_dir:
        mkdir(current_dir)

    return current_dir


def get_random_platform(platforms):
    """
    根据权重随机选择一个平台。
    """
    total_weight = sum(p["weight"] for p in platforms)

    if int(total_weight * 100) / 100 != 1:
        warnings.warn(f"平台权重总和应为1，当前为{total_weight:.2f}，将默认选择微博", UserWarning)
        return "微博"

    rand = random.uniform(0, total_weight)
    cumulative_weight = 0
    for platform in platforms:
        cumulative_weight += platform["weight"]
        if rand <= cumulative_weight:
            return platform["name"]


def extract_modified_article(raw_text):
    # 预处理：去除开头单独的html单词（包括大小写变体）
    raw_text = re.sub(r"^\s*html\b\s*", "", raw_text, flags=re.IGNORECASE)

    # 处理带html标记的代码块（允许未闭合）
    html_pattern = r"```html\s*([\s\S]*?)(?:\s*```|$)"
    # 处理无标记代码块（允许未闭合且匹配最后一个）
    code_pattern = r"```\s*([\s\S]*?)(?:\s*```|$)(?=[\s\S]*$)"

    html_match = re.search(html_pattern, raw_text)
    code_match = re.search(code_pattern, raw_text)

    if html_match:
        return html_match.group(1).strip()
    elif code_match:
        return code_match.group(1).strip()
    else:
        # 兜底逻辑：去除首尾反引号（包括连续多个反引号）
        return re.sub(r"^`+|`+$", "", raw_text).strip()


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

    except requests.exceptions.RequestException as e:
        log.print_log(f"下载图片失败：{image_url}，错误：{e}")
        return None
    except Exception as e:
        log.print_log(f"处理图片失败：{image_url}，错误：{e}")
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
            if element.strip() == "":
                element.extract()  # 移除空文本节点
            elif element.strip().startswith("<!--") and element.strip().endswith("-->"):
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
                    formatted_lines.append(child.prettify().strip())
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
        # 检查是否为网络 URL（以 http:// 或 https:// 开头）
        if file_url.startswith(("http://", "https://")):
            # 直接打开网络 URL
            webbrowser.open(file_url)
        else:
            # 视为本地文件路径，转换为 file:// 格式
            if not os.path.exists(file_url):
                return "文件不存在！"

            html_url = f"file://{os.path.abspath(file_url).replace(os.sep, '/')}"
            webbrowser.open(html_url)
        return ""
    except Exception as e:
        return str(e)


def is_valid_url(url):
    try:
        result = urlparse(url)
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


def get_template_dir():
    return get_res_path("templates", os.path.join(get_current_dir("knowledge", False)))


def get_all_categories(default_template_categories):
    """动态获取所有分类文件夹名称"""
    template_dir = get_template_dir()
    categories = []

    # 添加默认分类（确保存在）
    default_categories = list(default_template_categories.values())  # 使用中文名
    categories.extend(default_categories)

    # 扫描实际存在的文件夹
    if os.path.exists(template_dir):
        for item in os.listdir(template_dir):
            item_path = os.path.join(template_dir, item)
            if os.path.isdir(item_path) and item not in categories:
                categories.append(item)

    return sorted(categories)


def get_templates_by_category(category):
    """获取指定分类下的模板列表"""
    if not category or category == "随机分类":
        return []

    template_dir = get_template_dir()
    category_path = os.path.join(template_dir, category)

    if not os.path.exists(category_path):
        return []

    template_files = glob.glob(os.path.join(category_path, "*.html"))
    template_names = [os.path.splitext(os.path.basename(f))[0] for f in template_files]
    return sorted(template_names)


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


def remove_markdown_code_blocks(content):
    """
    移除所有Markdown代码块标识但保留内容
    处理以下格式：
      ```markdown 内容 ```
      ``` 内容 ```
      `内容`
    """
    # 移除多行代码块标识（带markdown标签）
    content = re.sub(r"```markdown\s*", "", content, flags=re.IGNORECASE)

    # 移除通用多行代码块标识
    content = re.sub(r"```\s*", "", content)

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


def extract_main_title(md_content):
    """提取Markdown文档主标题（增强版）
    参数:
        md_content: Markdown文本内容
    返回:
        匹配到的一级标题文本，若无则返回首行非空内容
    """
    # 优先匹配标准一级标题（如# Title）
    title_match = re.search(
        r"^#\s+(.+?)(?:\s+#+)?\s*$",  # 兼容标题尾部的#符号
        md_content,
        flags=re.MULTILINE,
    )

    if title_match:
        return title_match.group(1).strip()

    # 次优匹配首行非空内容（跳过YAML front matter等）
    first_line = next((line.strip() for line in md_content.splitlines() if line.strip()), None)

    return first_line if first_line else None


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
    # 检查是否为绝对路径
    if os.path.isabs(url):
        return True

    # 检查是否为相对路径
    if url.startswith("./") or url.startswith("../"):
        return True

    # 检查是否为网络URL
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https", "ftp"):
        return False

    # 其他情况视为本地路径
    return True


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
        img = img.resize((new_width, new_height), Image.LANCZOS)

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
