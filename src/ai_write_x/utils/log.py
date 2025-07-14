import logging
import sys
import re
import os
import time
import traceback
from datetime import datetime

from src.ai_write_x.utils import utils
from src.ai_write_x.utils import comm
from src.ai_write_x.config.config import Config


def strip_ansi_codes(text):
    """去除 ANSI 颜色代码"""
    ansi_pattern = r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    return re.sub(ansi_pattern, "", text)


class QueueLoggingHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        try:
            msg = self.format(record)
            msg = strip_ansi_codes(msg)  # 去除 ANSI 代码
            self.queue.put({"type": "status", "value": f"LOG: {msg}"})
        except Exception:
            self.handleError(record)


class QueueStreamHandler:
    def __init__(self, queue):
        self.queue = queue
        self.original_stdout = sys.__stdout__  # 保存原始 stdout

    def write(self, msg):
        if msg.strip():
            clean_msg = strip_ansi_codes(msg.rstrip())  # 移除尾部换行/空格
            self.queue.put({"type": "status", "value": f"PRINT: {clean_msg}"})
            if self.original_stdout is not None:  # 检查 stdout 是否可用
                self.original_stdout.write(msg.rstrip() + "\n")  # 强制换行
                self.original_stdout.flush()

    def flush(self):
        if self.original_stdout is not None:  # 检查 stdout 是否可用
            self.original_stdout.flush()

    def fileno(self):
        # 返回一个有效的文件描述符或引发适当的异常
        if self.original_stdout is not None:
            try:
                return self.original_stdout.fileno()
            except (AttributeError, IOError):
                pass
        raise IOError("Stream has no fileno")


def setup_logging(log_name, queue):
    """配置日志处理器，将 CrewAI 日志发送到队列"""
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    handler = QueueLoggingHandler(queue)
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False  # 避免重复日志
    for h in logger.handlers[:]:
        if isinstance(h, logging.StreamHandler) and h is not handler:
            logger.removeHandler(h)
    # 捕获 print 输出
    sys.stdout = QueueStreamHandler(queue)


# 支持多种日志文件
def get_log_path(log_name="log"):
    logs_path = utils.get_current_dir("logs")
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(logs_path, f"{log_name}_{timestamp}.log")


def print_log(msg, msg_type="status"):
    config = Config.get_instance()

    if config.ui_mode:
        comm.send_update(msg_type, msg)
    else:
        print(f"[{time.strftime('%H:%M:%S')}] [{msg_type.upper()}]: {msg}")


def print_traceback(what, e):
    error_traceback = traceback.format_exc()

    # 获取错误位置信息
    tb = e.__traceback__
    filename = tb.tb_frame.f_code.co_filename
    line_number = tb.tb_lineno

    ret = (
        f"{what}发生错误: {str(e)}\n错误位置: {filename}:{line_number}\n错误详情:{error_traceback}"
    )
    print(ret)
    return ret
