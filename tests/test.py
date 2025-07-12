# test.py

import sys
import os

import litellm  # noqa 402
from crewai import Agent, LLM
from crewai.cli.constants import ENV_VARS


# 获取当前文件（b.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到项目根目录（即 A 和 B 的父目录）
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径
sys.path.append(project_root)

from src.ai_auto_wxgzh.utils import log  # noqa 402
from src.ai_auto_wxgzh.utils import utils  # noqa 402
from src.ai_auto_wxgzh.tools.wx_publisher import pub2wx, WeixinPublisher  # noqa 402
from src.ai_auto_wxgzh.config.config import Config  # noqa 402


def test_llm_support():
    llm = None
    config = Config.get_instance()
    config.load_config()
    if not utils.is_llm_supported(config.api_type, config.api_key_name, ENV_VARS):
        llm = LLM(model=config.api_model, api_key=config.api_key)
    # 设置环境变量
    # os.environ[config.api_key_name] = "your-actual-deepseek-api-key"
    # os.environ["MODEL"] = config.api_model

    # 创建Agent测试
    agent = Agent(role="test role", goal="test goal", backstory="test backstory", llm=llm)

    # 检查LLM是否正确创建
    print(f"Agent LLM model: {agent.llm.model}")
    print(f"Agent LLM API key set: {'Yes' if agent.llm.api_key else 'No'}")


article = """"""

# 测试直接发布文章
# log.print_log(pub2wx(article, appid, appsecret, author))
# log.print_log(utils.decompress_html(article))
# log.print_log(utils.extract_html(article))

# 检查支持的模型
test_llm_support()

# print(utils.markdown_to_plaintext(article))

# print(utils.extract_modified_article(article))

config = Config.get_instance()
config.load_config()
publisher = WeixinPublisher(
    config.wechat_credentials[0]["appid"],
    config.wechat_credentials[0]["appsecret"],
    config.wechat_credentials[0]["author"],
)

print(publisher.is_verified)
print(config.get_sendall_by_appid(config.wechat_credentials[0]["appid"]))
