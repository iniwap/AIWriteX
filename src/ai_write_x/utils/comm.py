# comm.py
import queue

_command_queue = queue.Queue()
_update_queue = queue.Queue()


def send_update(msg_type, value):
    _update_queue.put({"type": msg_type, "value": value})


def get_update_queue():
    return _update_queue


def send_command(command):
    _command_queue.put(command)


def get_command_queue():
    return _command_queue
