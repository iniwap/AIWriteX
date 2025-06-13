#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""

主界面

"""

import time
import queue
import threading
import os
import glob
from collections import deque

import PySimpleGUI as sg
import tkinter as tk

from src.ai_auto_wxgzh.crew_main import autowx_gzh

from src.ai_auto_wxgzh.utils import comm
from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.utils import log
from src.ai_auto_wxgzh.config.config import Config

from src.ai_auto_wxgzh.gui import ConfigEditor


__author__ = "iniwaper@gmail.com"
__copyright__ = "Copyright (C) 2025 iniwap"
# __date__ = "2025/04/17"


class MainGUI(object):
    def __init__(self):
        self._log_list = []
        self._template_list = []
        self._is_running = False  # 跟踪任务状态
        self._update_queue = comm.get_update_queue()
        self._log_buffer = deque(maxlen=100)
        self._ui_log_path = log.get_log_path("UI")
        self._log_list = self.__get_logs()
        self._template_list = self.__get_templates()
        # 配置 CrewAI 日志处理器
        log.setup_logging("crewai", self._update_queue)
        # 终止信号和线程
        self._stop_event = threading.Event()
        self._crew_thread = None

        # 加载配置，不验证
        config = Config.get_instance()
        if not config.load_config():
            # 配置信息未填写，仅作提示，用户点击开始任务时才禁止操作并提示错误
            log.print_log(config.error_message, "error")

        # 设置主题
        sg.theme("systemdefault")

        menu_list = [
            ["配置", ["管理界面", "CrewAI文件", "AIPy文件"]],
            [
                "文件",
                ["日志", self._log_list, "模板", self._template_list, "文章"],
            ],
            ["帮助", ["帮助", "关于", "官网"]],
        ]

        layout = [
            [sg.Menu(menu_list, key="-MENU-")],
            [
                sg.Image(
                    s=(640, 160),
                    filename=utils.get_res_path("UI\\bg.png", os.path.dirname(__file__)),
                    key="-BG-IMG-",
                    expand_x=True,
                )
            ],
            [
                sg.Column(
                    [
                        [
                            sg.Text(
                                "自定义文章话题：",
                                size=(12, 1),
                                pad=((10, 5), (5, 2)),
                            ),
                            sg.InputText(
                                "",
                                key="-TOPIC_INPUT-",
                                disabled=True,
                                size=(30, 1),
                                pad=((5, 5), (5, 2)),
                                tooltip="输入自定义话题，或留空以获取热搜作为文章标题",
                            ),
                            sg.Checkbox(
                                "",
                                key="-CUSTOM_TOPIC-",
                                enable_events=True,
                                tooltip="勾选以启用自定义话题，否则自动获取热搜作为文章标题",
                                size=(2, 1),
                                pad=((5, 10), (5, 2)),
                            ),
                        ],
                        [
                            sg.Text(
                                "AI参考文章链接：",
                                size=(12, 1),
                                pad=((10, 5), (2, 5)),
                                tooltip="输入链接，生成文章将参考其内容",
                            ),
                            sg.InputText(
                                "",
                                key="-URLS_INPUT-",
                                disabled=True,
                                size=(30, 1),
                                tooltip="多个链接请用竖线(|)分隔，例如：http://site1.com|https://site2.com",
                                pad=((5, 5), (2, 5)),
                            ),
                            sg.Combo(
                                ["10%", "20%", "30%", "50%", "75%"],
                                default_value="30%",
                                key="-REFERENCE_RATIO-",
                                disabled=True,
                                size=(6, 1),
                                pad=((5, 10), (2, 5)),
                                tooltip="选择参考链接文章内容的借鉴比例",
                            ),
                        ],
                    ],
                    justification="center",
                    element_justification="left",
                    pad=(0, 0),
                )
            ],
            [
                sg.Push(),
                sg.Button(
                    button_text="开始执行",
                    size=(12, 2),
                    key="-START_BTN-",
                    pad=((10, 5), (5, 5)),
                ),
                sg.Button(
                    button_text="结束执行",
                    size=(12, 2),
                    key="-STOP_BTN-",
                    disabled=not self._is_running,
                    pad=((5, 10), (5, 5)),
                ),
                sg.Push(),
            ],
            [
                sg.Text("——" * 20, size=(60, 1), text_color="gray"),
                sg.Push(),
            ],
            [
                sg.Text("日志:", size=(6, 1), pad=((10, 5), (5, 5))),
                sg.Spin(
                    [10, 20, 50, 100, 200, 500, 1000],
                    initial_value=100,
                    key="-LOG_LIMIT-",
                    size=(6, 1),
                    pad=((5, 5), (5, 5)),
                ),
                sg.Button(
                    "设置显示条数",
                    key="-SET_LOG_LIMIT-",
                    size=(12, 1),
                    pad=((5, 5), (5, 5)),
                ),
                sg.Button(
                    "清空日志",
                    key="-CLEAR_LOG-",
                    size=(12, 1),
                    pad=((5, 10), (5, 5)),
                ),
            ],
            [
                sg.Push(),
                sg.Multiline(
                    size=(100, 18),
                    key="-STATUS-",
                    autoscroll=True,
                    pad=((10, 10), (5, 10)),
                ),
                sg.Push(),
            ],
        ]

        self._window = sg.Window(
            "微信公众号AI工具 v1.5",
            layout,
            default_element_size=(12, 1),
            size=(640, 640),
            icon=self.__get_icon(),
            finalize=True,
        )
        self._menu = self._window["-MENU-"].TKMenu

    def __get_icon(self):
        return utils.get_res_path("UI\\icon.ico", os.path.dirname(__file__))

    def __gui_config_start(self):
        ConfigEditor.gui_start()

    def __save_ui_log(self, log_entry):
        # 如果日志不存在，则更新日志列表
        need_update = False
        if not os.path.exists(self._ui_log_path):
            need_update = True

        with open(self._ui_log_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            f.flush()

        if need_update:
            self._log_list = self.__get_logs()

        return need_update

    def __get_templates(self, max_files=10):
        try:
            template_files_abs = glob.glob(
                os.path.join(
                    utils.get_res_path(
                        "templates",
                        os.path.join(utils.get_current_dir("knowledge", False)),
                    ),
                    "*.html",
                )
            )

            if not template_files_abs:
                return ["更多..."]

            # 提取文件名（不含路径），限制数量
            template_filenames = sorted(
                [
                    os.path.splitext(os.path.basename(path))[0]
                    for path in template_files_abs[:max_files]
                ]
            )
            if len(template_files_abs) > max_files:
                template_filenames.append("更多...")

            return template_filenames
        except Exception as e:  # noqa 841
            return ["更多..."]

    def __get_logs(self, max_files=5):
        try:
            # 获取所有 .log 文件
            log_files = glob.glob(os.path.join(utils.get_current_dir("logs"), "*.log"))
            if not log_files:
                return ["更多..."]

            # 按修改时间排序（降序）
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            # 提取文件名（不含路径），限制数量
            log_filenames = [os.path.basename(f) for f in log_files[:max_files]]
            if len(log_files) > max_files:
                log_filenames.append("更多...")

            return log_filenames
        except Exception as e:  # noqa 841
            return ["更多..."]

    def __update_menu(self):
        # 找到 "文件" 菜单的索引
        file_menu_index = None
        for i in range(self._menu.index(tk.END) + 1):
            if self._menu.entrycget(i, "label") == "文件":
                file_menu_index = i
                break

        if file_menu_index is None:
            return

        # 获取 "文件" 子菜单
        file_menu = self._menu.entrycget(file_menu_index, "menu")
        file_menu = self._menu.nametowidget(file_menu)

        # 找到 "日志" 子菜单的索引
        log_menu_index = None
        for i in range(file_menu.index(tk.END) + 1):
            if file_menu.entrycget(i, "label") == "日志":
                log_menu_index = i
                break

        if log_menu_index is None:
            return

        # 获取 "日志" 子菜单
        log_menu = file_menu.entrycget(log_menu_index, "menu")
        log_menu = file_menu.nametowidget(log_menu)

        # 清空 "日志" 子菜单
        log_menu.delete(0, tk.END)

        # 添加新的日志文件名
        for log_item in self._log_list:
            log_menu.add_command(
                label=log_item,
                command=lambda item=log_item: self._window.write_event_value(item, None),
            )

    # 处理消息队列
    def process_queue(self):
        try:
            msg = self._update_queue.get_nowait()
            if msg["type"] == "progress":
                self._window["-PROGRESS-"].update(f"{msg['value']}%")
                self._window["-PROGRESS_BAR-"].update(msg["value"])
            elif msg["type"] in ["status", "warning", "error"]:
                # 追加日志到缓冲区
                if msg["value"].startswith("PRINT:"):
                    log_entry = f"[{time.strftime('%H:%M:%S')}][PRINT]: {msg['value'][6:]}"
                elif msg["value"].startswith("FILE_LOG:"):
                    log_entry = f"[{time.strftime('%H:%M:%S')}][FILE]: {msg['value'][9:]}"
                elif msg["value"].startswith("LOG:"):
                    log_entry = f"[{time.strftime('%H:%M:%S')}][LOG]: {msg['value']}"
                else:
                    log_entry = (
                        f"[{time.strftime('%H:%M:%S')}] [{msg['type'].upper()}]: {msg['value']}"
                    )
                self._log_buffer.append(log_entry)
                if self.__save_ui_log(log_entry):
                    # 需要更新日志列表
                    self.__update_menu()

                # 更新 Multiline，显示所有日志
                self._window["-STATUS-"].update("\n".join(self._log_buffer), append=False)
                if msg["type"] == "status" and (
                    msg["value"].startswith("任务完成！") or msg["value"] == "CrewAI 任务被终止"
                ):
                    self._window["-START_BTN-"].update(disabled=False)
                    self._window["-STOP_BTN-"].update(disabled=True)
                    self._is_running = False
                    self._crew_thread = None
                elif msg["type"] == "error":
                    sg.popup_error(
                        f"任务错误: {msg['value']}",
                        title="错误",
                        icon=self.__get_icon(),
                        non_blocking=True,
                    )
                    self._window["-START_BTN-"].update(disabled=False)
                    self._window["-STOP_BTN-"].update(disabled=True)
                    self._is_running = False
                    self._crew_thread = None
                elif msg["type"] == "warning":
                    sg.popup(
                        f"出现错误但不影响运行，告警信息：{msg['value']}",
                        title="系统提示",
                        icon=self.__get_icon(),
                        non_blocking=True,
                    )
        except queue.Empty:
            pass

    def run(self):
        while True:
            event, values = self._window.read(timeout=100)
            if event == sg.WIN_CLOSED:  # always,  always give a way out!
                if self._is_running and self._crew_thread and self._crew_thread.is_alive():
                    self._stop_event.set()
                    self._crew_thread.join(timeout=2.0)
                    if self._crew_thread.is_alive():
                        log.print_log("警告：任务终止超时，可能未完全停止")
                    else:
                        log.print_log("CrewAI 任务被终止（程序退出）")
                break
            elif event == "管理界面":
                self.__gui_config_start()
            elif event == "CrewAI文件":
                try:
                    os.system("start /B  notepad " + Config.get_instance().get_config_path())
                except Exception as e:
                    sg.popup(
                        "无法打开CrewAI配置文件 :( \n错误信息：" + str(e),
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
            elif event == "AIPy文件":
                try:
                    os.system("start /B  notepad " + Config.get_instance().get_aipy_config_path())
                except Exception as e:
                    sg.popup(
                        "无法打开AIPy配置文件 :( \n错误信息：" + str(e),
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
            elif event == "-CUSTOM_TOPIC-":
                # 根据复选框状态启用/禁用输入框和下拉框
                self._window["-TOPIC_INPUT-"].update(disabled=not values["-CUSTOM_TOPIC-"])
                self._window["-URLS_INPUT-"].update(disabled=not values["-CUSTOM_TOPIC-"])
                self._window["-REFERENCE_RATIO-"].update(disabled=not values["-CUSTOM_TOPIC-"])
            elif event == "-START_BTN-":
                config = Config.get_instance()
                if not config.validate_config():
                    sg.popup_error(
                        f"无法执行，配置错误：{config.error_message}",
                        title="系统提示",
                        icon=self.__get_icon(),
                        non_blocking=True,
                    )
                    continue
                elif not self._is_running:
                    # 处理自定义话题、链接和借鉴比例
                    if values["-CUSTOM_TOPIC-"]:
                        topic = values["-TOPIC_INPUT-"].strip()
                        if not topic:
                            sg.popup_error(
                                "自定义话题不能为空",
                                title="系统提示",
                                icon=self.__get_icon(),
                                non_blocking=True,
                            )
                            continue
                        config.custom_topic = topic
                        urls_input = values["-URLS_INPUT-"].strip()
                        if urls_input:
                            urls = [url.strip() for url in urls_input.split("|") if url.strip()]
                            valid_urls = [url for url in urls if utils.is_valid_url(url)]
                            if len(valid_urls) != len(urls):
                                sg.popup_error(
                                    "存在无效的URL，请检查输入（确保使用http://或https://）",
                                    title="系统提示",
                                    icon=self.__get_icon(),
                                    non_blocking=True,
                                )
                                continue
                            config.urls = valid_urls
                        else:
                            config.urls = []
                        # 将比例转换为浮点数
                        config.reference_ratio = float(values["-REFERENCE_RATIO-"].strip("%")) / 100
                    else:
                        config.custom_topic = ""
                        config.urls = []
                        config.reference_ratio = 0.0  # 重置为0
                    sg.popup(
                        "更多界面功能开发中，敬请期待 :)\n" "点击OK开始执行",
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
                    self._window["-START_BTN-"].update(disabled=True)
                    self._window["-STOP_BTN-"].update(disabled=False)
                    self._is_running = True
                    self._stop_event.clear()
                    self._crew_thread = threading.Thread(
                        target=autowx_gzh,
                        args=(self._stop_event, True),
                        daemon=True,
                    )
                    self._crew_thread.start()
                    # 记录任务开始日志
                    log.print_log(
                        f"开始任务，话题：{config.custom_topic or '热门话题'}"
                        + (
                            f"，链接：{config.urls}，借鉴比例：{config.reference_ratio*100:.0f}%"
                            if config.custom_topic
                            else ""
                        )
                    )
            elif event == "-STOP_BTN-":
                if self._is_running and self._crew_thread and self._crew_thread.is_alive():
                    self._stop_event.set()
                    self._crew_thread.join(timeout=2.0)
                    if self._crew_thread.is_alive():
                        log.print_log("警告：任务终止超时，可能未完全停止")
                    else:
                        log.print_log("CrewAI 任务被终止")
                    self._crew_thread = None
                    self._window["-START_BTN-"].update(disabled=False)
                    self._window["-STOP_BTN-"].update(disabled=True)
                    self._is_running = False
                    sg.popup(
                        "任务已终止",
                        title="系统提示",
                        icon=self.__get_icon(),
                        non_blocking=True,
                    )
            elif event == "关于":
                sg.popup(
                    "关于软件",
                    "当前Version 1.1",
                    "Copyright (C) 2025 iniwap,All Rights Reserved",
                    title="系统提示",
                    icon=self.__get_icon(),
                )
            elif event == "官网":
                utils.open_url("https://github.com/iniwap")
            elif event == "帮助":
                sg.popup(
                    "———————————配置说明———————————\n"
                    "1、微信公众号AppID，AppSecrect必填（至少一个）\n"
                    "2、CrewAI使用的API的API KEY必填（使用的）\n"
                    "3、AIPy的模型提供商的API KEY必填（使用的）\n"
                    "4、其他使用默认即可，根据需求填写\n"
                    "———————————操作说明———————————\n"
                    "1、打开配置界面，首先进行必要的配置\n"
                    "2、点击开始执行，AI自动开始工作\n"
                    "3、陆续加入更多操作中...\n"
                    "———————————功能说明———————————\n"
                    "1、文件->日志：查看日志文件\n"
                    "2、文件->模板：查看内置模板文件\n"
                    "3、文件->文章：查看生成的文章\n"
                    "4、配置->CrewAI/AIPy：直接查看或编辑配置文件\n"
                    "5、部分界面内容，悬停会有提示",
                    title="使用帮助",
                    icon=self.__get_icon(),
                )
            elif event == "-SET_LOG_LIMIT-":
                self._log_buffer = deque(self._log_buffer, maxlen=values["-LOG_LIMIT-"])
                self._window["-STATUS-"].update("\n".join(self._log_buffer))
            elif event == "-CLEAR_LOG-":
                self._log_buffer.clear()
                self._window["-STATUS-"].update("")
            elif event in self._log_list:
                if event == "更多...":
                    logs_path = utils.get_current_dir("logs")

                    filename = sg.popup_get_file(
                        "打开文件",
                        default_path=logs_path,
                        file_types=(("log文件", "*.log"),),
                        no_window=True,
                    )

                    if len(filename) == 0:
                        continue

                    try:
                        os.system("start /B  notepad " + filename)
                    except Exception as e:
                        sg.popup(
                            "无法打开日志文件 :( \n错误信息：" + str(e),
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
                else:
                    try:
                        os.system(
                            "start /B  notepad "
                            + os.path.join(utils.get_current_dir("logs"), event)
                        )
                    except Exception as e:
                        sg.popup(
                            "无法打开日志文件 :( \n错误信息：" + str(e),
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
            elif event in self._template_list:
                template_dir_abs = utils.get_res_path(
                    "templates",
                    os.path.join(utils.get_current_dir("knowledge", False)),
                )
                if event == "更多...":
                    filename = sg.popup_get_file(
                        "打开文件",
                        default_path=template_dir_abs,
                        file_types=(("模板文件", "*.html"),),
                        no_window=True,
                    )

                    if len(filename) == 0:
                        continue

                    if ret := utils.open_url(filename):
                        sg.popup(
                            "无法打开模板 :( \n错误信息：" + ret,
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
                else:
                    if ret := utils.open_url(os.path.join(template_dir_abs, f"{event}.html")):
                        sg.popup(
                            "无法打开模板 :( \n错误信息：" + ret,
                            title="系统提示",
                            icon=self.__get_icon(),
                        )

            elif event == "文章":
                # 生成的最终文章
                final_article = os.path.join(utils.get_current_dir(), "final_article.html")
                if ret := utils.open_url(final_article):
                    sg.popup(
                        "无法查看，请先执行并生成文章！:( \n错误信息：" + ret,
                        title="系统提示",
                        icon=self.__get_icon(),
                    )

            # 处理队列更新（非阻塞）
            if self._is_running:
                self.process_queue()


def gui_start():
    MainGUI().run()


if __name__ == "__main__":
    gui_start()
