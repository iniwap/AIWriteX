import queue
import time


_command_queue = queue.Queue()
_update_queue = queue.Queue()


def get_update_queue():
    return _update_queue


def send_command(command):
    _command_queue.put(command)


def get_command_queue():
    return _command_queue


_web_log_queue = None


def set_log_queue(queue):
    """设置 Web 日志队列"""
    global _web_log_queue
    _web_log_queue = queue


def send_update(msg_type, msg):
    """发送更新消息"""

    # 如果设置了 Web 队列,优先发送到该队列
    if _web_log_queue is not None:
        try:
            _web_log_queue.put({"type": msg_type, "message": msg, "timestamp": time.time()})
            return
        except Exception:
            pass
    else:
        _update_queue.put({"type": msg_type, "value": msg})
