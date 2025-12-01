#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import platform
import threading
from pathlib import Path
from . import utils


class WindowIconManager:
    """窗口图标管理器"""

    def __init__(self):
        self.icon_path = self._get_icon_path()

    def _get_icon_path(self):
        """获取适合当前平台的图标文件路径"""
        gui_dir = Path(__file__).parent.parent / "assets"

        if platform.system() == "Windows":
            return utils.get_res_path("UI/icon.ico", str(gui_dir))
        elif platform.system() == "Darwin":  # macOS
            return utils.get_res_path("UI/icon.png", str(gui_dir))
        else:  # Linux
            return utils.get_res_path("UI/icon.png", str(gui_dir))

    def set_window_icon_windows(self, window_title="AIWriteX"):
        """Windows 平台设置窗口图标"""
        if platform.system() != "Windows" or not Path(self.icon_path).exists():
            return

        try:
            import win32gui
            import win32con

            # 查找窗口句柄
            hwnd = None

            def enum_windows_proc(hwnd, lParam):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_title in window_text:
                        lParam.append(hwnd)
                return True

            windows = []
            win32gui.EnumWindows(enum_windows_proc, windows)
            if windows:
                hwnd = windows[0]

                if hwnd:
                    # 加载图标
                    icon = win32gui.LoadImage(
                        0,
                        str(self.icon_path),
                        win32con.IMAGE_ICON,
                        0,
                        0,
                        win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE,
                    )

                    if icon:
                        # 设置窗口图标（标题栏和任务栏）
                        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, icon)
                        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, icon)

                        # 强制刷新任务栏图标
                        win32gui.SetWindowPos(
                            hwnd,
                            0,
                            0,
                            0,
                            0,
                            0,
                            win32con.SWP_NOMOVE
                            | win32con.SWP_NOSIZE
                            | win32con.SWP_NOZORDER
                            | win32con.SWP_FRAMECHANGED,
                        )

                        # 强制重绘
                        win32gui.InvalidateRect(hwnd, None, True)
                        win32gui.UpdateWindow(hwnd)

        except Exception:
            pass

    def setup_icon_async(self, window_title="AIWriteX"):
        """异步设置图标"""
        if platform.system() == "Windows":
            threading.Thread(
                target=self.set_window_icon_windows, args=(window_title,), daemon=True
            ).start()
