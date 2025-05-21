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
from src.ai_auto_wxgzh.utils import log


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


def get_is_release_ver():
    if getattr(sys, "frozen", None):
        return True
    else:
        return False


def get_res_path(file_name, basedir=""):
    if get_is_release_ver():
        return os.path.join(sys._MEIPASS, file_name)

    return os.path.join(basedir, file_name)


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


def extract_modified_article(content):
    match = re.search(r"```(?:html)?\s*([\s\S]*?)```", content, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        # 分别去除开头和结尾的反引号（保留其他字符）
        stripped = content.strip()
        stripped = stripped.lstrip("`").rstrip("`")
        return stripped.strip()  # 最后再去除可能的空白


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


def extract_image_urls(html_content):
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
    return list(set(urls))


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

    except Exception as e:
        # 错误处理：解析失败时返回原始内容
        print(f"HTML 格式化错误：{e}")
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
