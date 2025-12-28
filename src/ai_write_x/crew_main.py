#!/usr/bin/env python
import os
import warnings
import multiprocessing
import signal
import time
import json

from src.ai_write_x.utils.path_manager import PathManager
from src.ai_write_x.tools import hotnews
from src.ai_write_x.utils import utils
from src.ai_write_x.utils import log
from src.ai_write_x.config.config import Config
from src.ai_write_x.core.system_init import setup_aiwritex


warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.*")

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"


def run_crew_in_process(inputs, log_queue, base_config, aiforge_config, config_data=None):
    """在独立进程中运行 CrewAI 工作流"""

    env_file_path = ""
    try:
        # 设置信号处理器
        def signal_handler(signum, frame):
            log_queue.put(
                {"type": "system", "message": "收到终止信号，正在退出", "timestamp": time.time()}
            )
            os._exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # 设置进程专用日志系统
        log.setup_process_logging(log_queue)
        # 设置进程间日志队列
        log.set_process_queue(log_queue)

        # 恢复环境变量
        env_file_path = None
        if config_data and "env_file_path" in config_data:
            env_file_path = config_data["env_file_path"]
            try:
                if os.path.exists(env_file_path):
                    with open(env_file_path, "r", encoding="utf-8") as f:
                        parent_env = json.load(f)

                    # 更新当前进程的环境变量
                    os.environ.update(parent_env)
                else:
                    pass
            except Exception:
                pass

        # 获取子进程的 Config 实例
        config = Config.get_instance()
        config.config = base_config
        config.aiforge_config = aiforge_config

        # 同步主进程的配置数据到子进程
        if config_data:
            for key, value in config_data.items():
                # 跳过环境文件路径，这个不是配置属性
                if key != "env_file_path":
                    setattr(config, key, value)

        # 添加调试信息
        log.print_log(f"任务参数：API类型={config.api_type}，模型={config.api_model} ", "status")

        # 执行任务
        result = run(inputs)

        # 发送成功消息
        log_queue.put(
            {
                "type": "internal",
                "message": "任务执行完成",
                "result": result,
                "timestamp": time.time(),
            }
        )

    except Exception as e:
        # 发送失败消息到队列
        log_queue.put({"type": "error", "message": str(e), "timestamp": time.time()})

        # 发送internal类型的失败标记
        log_queue.put(
            {
                "type": "internal",
                "message": "任务执行失败",
                "error": str(e),
                "timestamp": time.time(),
            }
        )

    finally:
        # 清理环境变量文件
        if env_file_path and os.path.exists(env_file_path):
            try:
                os.remove(env_file_path)
            except Exception:
                pass

        time.sleep(0.5)
        os._exit(0)


def run(inputs):
    """
    Run the crew.
    """
    try:
        workflow = setup_aiwritex()

        # 提取参数
        topic = inputs.get("topic", "")

        # 准备kwargs参数
        kwargs = {
            "platform": inputs.get("platform", ""),
            "urls": inputs.get("urls", []),
            "reference_ratio": inputs.get("reference_ratio", 0.0),
        }

        return workflow.execute(topic=topic, **kwargs)

    except Exception as e:
        log.print_traceback("", e)
        raise


def ai_write_x_run(config_data=None):
    """执行 AI 写作任务"""
    config = Config.get_instance()

    # 准备输入参数
    log.print_log("[PROGRESS:INIT:START]", "internal")

    if not config.custom_topic:
        # 热搜模式: 自动获取热搜话题
        platform = utils.get_random_platform(config.platforms)
        topic = hotnews.select_platform_topic(platform, 5)
        urls = []
        reference_ratio = 0.0
    else:
        topic = config.custom_topic
        if config_data and config_data.get("platform"):
            # 热搜模式(WEB前端传入)
            platform = config_data.get("platform")
            urls = []
            reference_ratio = 0.0
        else:
            # 借鉴模式: 使用自定义话题
            urls = config.urls
            reference_ratio = config.reference_ratio
            platform = ""  # 借鉴模式下 platform 为空

    inputs = {
        "platform": platform,
        "topic": topic,
        "urls": urls,
        "reference_ratio": reference_ratio,
    }

    if config_data:
        try:
            log_queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=run_crew_in_process,
                args=(inputs, log_queue, config.get_config(), config.aiforge_config, config_data),
                daemon=False,
            )
            return process, log_queue
        except Exception as e:
            log.print_log(str(e), "error")
            return None, None
    else:
        # 非 UI 模式直接执行
        try:
            result = run(inputs)
            log.print_log("任务完成！")
            return True, result
        except Exception as e:
            log.print_log(f"执行出错：{str(e)}", "error")
            return False, None


def ai_write_x_main(config_data=None):
    """主入口函数"""
    config = Config.get_instance()
    # 如果是 UI 启动会传递配置数据，应用到当前进程
    if config_data:
        for key, value in config_data.items():
            setattr(config, key, value)
    else:
        # 非UI启动，不传递config_data，需要验证配置
        if not config.load_config():
            log.print_log("加载配置失败，请检查是否有配置！", "error")
            return None, None

        if not config.validate_config():
            log.print_log(f"配置填写有错误：{config.error_message}", "error")
            return None, None

    task_model = "自定义" if not config.platform else "热搜随机"
    log.print_log(f"开始执行任务，话题模式：{task_model}")

    # 保存环境变量到临时文件
    if config_data:
        env_file = PathManager.get_temp_dir() / f"env_{os.getpid()}.json"
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                json.dump(dict(os.environ), f, ensure_ascii=False, indent=2)

            # 将环境文件路径添加到config_data
            if config_data is None:
                config_data = {}
            config_data["env_file_path"] = str(env_file)

        except Exception:
            pass

    # 设置环境变量
    os.environ[config.api_key_name] = config.api_key
    os.environ["MODEL"] = config.api_model
    os.environ["OPENAI_API_BASE"] = config.api_apibase

    # 直接启动内容生成，不处理发布
    return ai_write_x_run(config_data=config_data)


if __name__ == "__main__":
    if not utils.get_is_release_ver():
        ai_write_x_main()
