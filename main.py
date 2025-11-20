#!/usr/bin/python
# -*- coding: UTF-8 -*-

import platform
import multiprocessing
import sys
import os
import ctypes

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"

from aiforge import AIForgeEngine  # noqa


def is_admin():
    """检查是否具有管理员权限（跨平台）"""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin()
        elif platform.system() == "Darwin":  # macOS
            return True
        elif platform.system() == "Linux":
            return os.getuid() == 0
        else:
            return True
    except Exception:
        return False


def run():
    """启动GUI应用程序"""
    try:
        # 调用授权模块接口
        from src.ai_write_x.license import check_license_and_start

        check_license_and_start()

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"启动失败: {str(e)}")


def admin_run():
    """以管理员权限运行（跨平台）"""
    if platform.system() == "Windows":
        if is_admin():
            run()
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 0)
    else:
        run()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)

    # 检查是否为AIForge子进程，传递执行环境
    if AIForgeEngine.handle_sandbox_subprocess(
        globals_dict=globals().copy(), sys_path=sys.path.copy()
    ):
        sys.exit(0)
    else:
        # 正常启动逻辑
        if len(sys.argv) > 1:
            if sys.argv[1] == "-d":
                run()
        else:
            admin_run()
