#!/usr/bin/env python
import sys
import os
import warnings
import asyncio

from src.ai_auto_wxgzh.tools import hotnews
from src.ai_auto_wxgzh.crew import AutowxGzh
from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.utils import log
from src.ai_auto_wxgzh.config.config import Config


warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


# 为了能结束任务，需要异步执行
class StopCrewException(Exception):
    """自定义异常，用于中断 CrewAI"""

    pass


async def run_crew_async(stop_event, inputs, appid, appsecret, author):
    """异步运行 CrewAI，检查终止信号"""
    try:
        if stop_event.is_set():
            raise StopCrewException("CrewAI 任务被终止")
        result = await AutowxGzh(appid, appsecret, author).crew().kickoff_async(inputs=inputs)
        return result
    except StopCrewException as e:
        raise e
    except Exception as e:
        raise e


def run(inputs, appid, appsecret, author):
    """
    Run the crew.
    """
    try:
        AutowxGzh(appid, appsecret, author).crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def autowx_gzh(stop_event=None, ui_mode=False):
    config = Config.get_instance()
    if not ui_mode:
        if not config.load_config():
            log.print_log("加载配置失败，请检查是否有配置！")
            return
        elif not config.validate_config():
            log.print_log(f"配置填写有错误：{config.error_message}")
            return

    # 设置模式
    config.ui_mode = ui_mode

    os.environ[config.api_key_name] = config.api_key
    os.environ["MODEL"] = config.api_model
    os.environ["OPENAI_API_BASE"] = config.api_apibase

    for credential in config.wechat_credentials:
        appid = credential["appid"]
        appsecret = credential["appsecret"]
        author = credential["author"]

        # 如果没用配置appid，则忽略该条
        if len(appid) == 0 or len(appsecret) == 0:
            continue

        if not config.custom_topic:
            platform = utils.get_random_platform(config.platforms)
            topic = hotnews.select_platform_topic(platform, 5)  # 前五个热门话题根据一定权重选一个
            urls = []
            reference_ratio = 0
        else:
            topic = config.custom_topic
            urls = config.urls
            reference_ratio = config.reference_ratio
            platform = ""
        inputs = {
            "platform": platform,
            "topic": topic,
            "urls": urls,
            "reference_ratio": reference_ratio,
            "min_article_len": config.min_article_len,
            "max_article_len": config.max_article_len,
        }

        log.print_log("CrewAI开始工作...")
        if ui_mode:
            try:
                # 运行异步 kickoff
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        run_crew_async(stop_event, inputs, appid, appsecret, author)
                    )
                    log.print_log("任务完成！")
                finally:
                    loop.close()
            except StopCrewException as e:
                log.print_log(f"执行出错：{str(e)}")
            except Exception as e:
                log.print_log(str(e), "error")
        else:
            try:
                run(inputs, appid, appsecret, author)
                log.print_log("任务完成！")
            except Exception as e:
                log.print_log(f"执行出错：{str(e)}")


# ----------------由于参数原因，以下调用不可用------------------
def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        AutowxGzh().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AutowxGzh().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        AutowxGzh().crew().test(
            n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    autowx_gzh()
