import sys
import os


# 获取当前文件（b.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到项目根目录（即 A 和 B 的父目录）
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径
sys.path.append(project_root)

from src.ai_auto_wxgzh.tools.search_template import search_web, extract_urls_content  # noqa 401


if __name__ == "__main__":

    print(search_web("竹节虫"))
