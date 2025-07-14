import sys
import os

# 获取当前文件（b.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到项目根目录（即 A 和 B 的父目录）
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径
sys.path.append(project_root)

from src.ai_write_x.utils import log  # noqa 402
from src.ai_write_x.tools.hotnews import select_platform_topic  # noqa 402


selected_topic = select_platform_topic("微博")
log.print_log(f"热门话题: {selected_topic}")
