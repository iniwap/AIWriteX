# test.py

import sys
import os

# 获取当前文件（b.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到项目根目录（即 A 和 B 的父目录）
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径
sys.path.append(project_root)

from src.ai_auto_wxgzh.utils import log  # noqa 402
from src.ai_auto_wxgzh.utils import utils  # noqa 402
from src.ai_auto_wxgzh.tools.wx_publisher import pub2wx  # noqa 402
from src.ai_auto_wxgzh.config.config import Config  # noqa 402

article = """"""

# 测试直接发布文章
# log.print_log(pub2wx(article, appid, appsecret, author))
log.print_log(utils.decompress_html(article))
# log.print_log(utils.extract_html(article))
