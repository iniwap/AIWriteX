#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
文章管理界面，独立窗口，负责文章的显示、编辑、预览、发布和删除
支持临时添加微信公众号配置，仅用于当前会话
"""

import os
import glob
import time
import PySimpleGUI as sg
import subprocess
import json

from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.config.config import Config
from src.ai_auto_wxgzh.tools.wx_publisher import pub2wx

__author__ = "iniwaper@gmail.com"
__copyright__ = "Copyright (C) 2025 iniwap"
__date__ = "2025/06/23"


class ArticleManager:
    def __init__(self):
        """初始化文章管理窗口"""
        self._publishing = False
        self._window = None
        self._articles = self._get_articles()  # 文章列表
        self._config = Config.get_instance()  # 配置实例
        self._credentials = self._get_credentials()  # 预存微信公众号配置
        self._temp_credentials = []  # 临时配置，仅当前会话有效
        sg.theme("systemdefault")  # 与主界面一致

    def _get_publish_status(self, title):
        """获取文章发布状态"""
        publish_file = os.path.join(utils.get_article_dir(), "publish_records.json")
        try:
            if os.path.exists(publish_file):
                with open(publish_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    if title in records and records[title]:
                        # 获取最近一次发布记录
                        latest_record = max(records[title], key=lambda x: x["publish_time"])
                        if latest_record["success"]:
                            return {"status": "published", "records": records[title]}
                        else:
                            return {"status": "failed", "records": records[title]}
        except Exception:
            pass

        return {"status": "unpublished", "records": []}

    def _save_publish_record(
        self, title, appid, author, publish_time, success=True, error_msg=None
    ):
        """保存发布记录"""
        publish_file = os.path.join(utils.get_article_dir(), "publish_records.json")
        try:
            records = {}
            if os.path.exists(publish_file):
                with open(publish_file, "r", encoding="utf-8") as f:
                    records = json.load(f)

            if title not in records:
                records[title] = []

            record = {
                "appid": appid,
                "author": author,
                "publish_time": publish_time,
                "success": success,
            }
            if not success and error_msg:
                record["error"] = error_msg

            records[title].append(record)

            with open(publish_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_articles(self):
        """获取所有文章文件，返回标题、路径、创建时间、文件大小、发布状态"""
        try:
            article_files = glob.glob(os.path.join(utils.get_article_dir(), "*.html"))
            articles = []
            for path in article_files:
                basename = os.path.basename(path)
                title = os.path.splitext(basename)[0].replace("_", "|")
                stats = os.stat(path)
                create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats.st_ctime))
                size = f"{stats.st_size / 1024:.2f} KB"

                # 检查发布状态
                publish_status = self._get_publish_status(title)
                status_text = {
                    "published": "已发布",
                    "failed": "发布失败",
                    "unpublished": "未发布",
                }[publish_status["status"]]

                articles.append(
                    {
                        "title": title,
                        "path": path,
                        "create_time": create_time,
                        "size": size,
                        "status": publish_status["status"],
                        "status_text": status_text,
                        "publish_records": publish_status["records"],
                    }
                )
            return sorted(articles, key=lambda x: x["create_time"], reverse=True)
        except Exception:
            return []

    def _get_credentials(self):
        """获取预存的微信公众号配置，仅返回appid不为空的"""
        try:
            credentials = [
                {"appid": c["appid"], "appsecret": c["appsecret"], "author": c["author"]}
                for c in self._config.wechat_credentials
                if c["appid"].strip() != ""
            ]
            return credentials
        except Exception:
            return []

    def _add_temp_credential(self, appid, appsecret, author):
        """添加临时微信公众号配置"""
        if not appid or not appsecret or not author:
            sg.popup_error(
                "AppID、AppSecret 和 作者 不能为空",
                title="系统提示",
                icon=self.__get_icon(),
            )
            return False
        self._temp_credentials.append({"appid": appid, "appsecret": appsecret, "author": author})
        sg.popup(
            "临时配置已添加，可在上方选择",
            non_blocking=True,
            title="系统提示",
            icon=self.__get_icon(),
        )
        return True

    def _edit_article(self, path, title):
        """编辑文章，指定应用打开"""
        if not os.path.exists(path):
            sg.popup_error(
                f"文章文件不存在：{title}",
                title="系统提示",
                icon=self.__get_icon(),
            )
            return

        editors = [
            "cursor",  # Cursor AI 代码编辑器
            "trae",  # Trae AI 代码编辑器
            "windsurf",  # Windsurf AI 代码编辑器
            "zed",  # Zed Editor
            "tabby",  # TabbyML
            "code",  # Visual Studio Code
            "subl",  # Sublime Text
            "notepad++",  # Notepad++
            "webstorm",  # WebStorm
            "phpstorm",  # PhpStorm
            "pycharm",  # PyCharm
            "idea",  # IntelliJ IDEA
            "brackets",  # Brackets
            "gvim",  # Vim（图形界面）
            "emacs",  # Emacs
            "notepad",  # Windows 记事本
        ]

        for editor_cmd in editors:
            try:
                subprocess.run(
                    f'{editor_cmd} "{path}"',
                    shell=True,
                    check=True,
                    stderr=subprocess.DEVNULL,
                )

                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

    def _view_article(self, path, title):
        """预览文章，在浏览器中打开"""
        if os.path.exists(path):
            if utils.open_url(path):
                sg.popup_error(
                    f"无法预览文章：{title}",
                    title="系统提示",
                    icon=self.__get_icon(),
                )
        else:
            sg.popup_error(
                f"文章文件不存在：{title}",
                title="系统提示",
                icon=self.__get_icon(),
            )

    def _publish_article(self, article, title, digest, credentials):
        """发布文章到指定微信公众号"""
        results = []
        for credential in credentials:
            appid = credential["appid"]
            author = credential["author"]
            appsecret = credential["appsecret"]

            # 不保存最终发布到微信的文章
            result, _, success = pub2wx(title, digest, article, appid, appsecret, author)
            publish_time = time.strftime("%Y-%m-%d %H:%M:%S")

            # 保存发布记录
            if success:
                self._save_publish_record(title, appid, author, publish_time, True)
            else:
                self._save_publish_record(title, appid, author, publish_time, False, result)

            results.append(
                {
                    "title": title,
                    "appid": appid,
                    "author": author,
                    "success": success,
                    "result": result,
                }
            )

        return results

    def _delete_article(self, path, title):
        """删除文章文件"""
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                sg.popup_error(
                    f"无法删除文章：{title}",
                    title="系统提示",
                    icon=self.__get_icon(),
                )
        else:
            sg.popup_error(
                f"文章文件不存在：{title}",
                title="系统提示",
                icon=self.__get_icon(),
            )

    def _create_layout(self):
        """创建文章管理窗口布局"""
        headings = ["序号", "标题", "创建时间", "文件大小", "发布状态"]
        data = self._build_table_data()
        right_click_menu = ["", ["编辑", "预览", "发布", "删除"]]

        # 区分固定和临时配置，临时配置加 [临时] 标记
        credential_options = (
            [f"{c['author']} ({c['appid']})" for c in self._credentials]
            + [f"[临时]{c['author']} ({c['appid']})" for c in self._temp_credentials]
        ) or ["无配置"]

        config_layout = [
            [
                sg.Text(
                    "微信公众号配置（支持多选）",
                    size=(25, 1),
                    font=("Microsoft YaHei", 10, "bold"),
                )
            ],
            [
                sg.Listbox(
                    values=credential_options,
                    key="-CONFIGS-",
                    size=(30, 12),
                    select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    enable_events=True,
                    tooltip="单击选中，再次单击取消选中",
                )
            ],
            [
                sg.Text(
                    "添加临时配置（仅本次使用）", size=(25, 1), font=("Microsoft YaHei", 10, "bold")
                )
            ],
            [
                sg.Text("AppID：", size=(8, 1)),
                sg.Input("", key="-APPID-", size=(20, 1)),
            ],
            [
                sg.Text("AppSecret：", size=(8, 1)),
                sg.Input("", key="-APPSECRET-", size=(20, 1)),
            ],
            [
                sg.Text("作者：", size=(8, 1)),
                sg.Input("", key="-AUTHOR-", size=(20, 1)),
            ],
            [
                sg.Push(),
                sg.Button("添加", key="-ADD_CONFIG-", size=(6, 1)),
            ],
            [
                sg.Text(
                    "发布记录（最后选中的文章）",
                    size=(25, 1),
                    font=("Microsoft YaHei", 10, "bold"),
                )
            ],
            [
                sg.Multiline(
                    "",
                    key="-PUBLISH_HISTORY-",
                    size=(30, 8),
                    disabled=True,
                    autoscroll=False,
                    font=("Microsoft YaHei", 9),
                )
            ],
        ]
        layout = [
            [
                sg.Column(
                    [
                        [
                            sg.Input("", key="-SEARCH-", size=(20, 1), tooltip="按标题搜索"),
                            sg.Button("搜索", key="-SEARCH_BTN-", size=(8, 1)),
                            sg.Button("刷新", key="-REFRESH-", size=(8, 1)),
                            sg.Push(),
                            sg.Button(
                                "批量删除",
                                key="-BATCH_DELETE-",
                                size=(10, 1),
                            ),
                        ],
                        [
                            sg.Table(
                                values=data,
                                headings=headings,
                                max_col_width=50,
                                auto_size_columns=False,  # 禁用自动调整列宽
                                col_widths=[
                                    5,
                                    30,
                                    18,
                                    10,
                                    8,
                                ],
                                justification="center",
                                key="-TABLE-",
                                enable_events=True,
                                select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                                right_click_menu=right_click_menu,
                                expand_x=True,
                                expand_y=True,
                                alternating_row_color="#e0e0e0",
                                tooltip="1. 右键选择操作 \n2. 单击选中 / Ctrl+单击或 Shift+单击多选\n3. 双击预览文章",
                            )
                        ],
                        [
                            sg.Push(),
                            sg.Button(
                                "发布选中文章",
                                key="-PUBLISH_SELECTED-",
                                size=(15, 1),
                                tooltip="发布选中的文章到指定公众号（按住Ctrl或Shift多选）",
                            ),
                            sg.Push(),
                        ],
                    ],
                    expand_x=True,
                    expand_y=True,
                ),
                sg.VerticalSeparator(),
                sg.Column(config_layout, vertical_alignment="top", pad=((10, 10), (10, 10))),
            ]
        ]
        return layout

    def _update_publish_history(self, article):
        """更新发布记录显示"""
        if article["publish_records"]:
            short_title = (
                article["title"][:10] + "..." if len(article["title"]) > 10 else article["title"]
            )
            history_text = f"《{short_title}》发布记录:\n"

            # 按时间倒序排序，最新的记录在前面
            sorted_records = sorted(
                article["publish_records"], key=lambda x: x["publish_time"], reverse=True
            )

            for index, record in enumerate(sorted_records, start=1):
                status_icon = "✓" if record.get("success", True) else "✗"
                date_only = record["publish_time"][:10]  # 只显示日期
                appid_last4 = "..." + record["appid"][-4:]  # 只显示AppID后4位

                history_text += (
                    f"{index}.{status_icon} {record['author']}({appid_last4}) {date_only}\n"
                )

                # 如果失败，显示错误信息（截断）
                if not record.get("success", True) and record.get("error"):
                    error_short = (
                        record["error"][:18] + "..."
                        if len(record["error"]) > 18
                        else record["error"]
                    )
                    history_text += f"   错误: {error_short}\n"
        else:
            short_title = (
                article["title"][:10] + "..." if len(article["title"]) > 10 else article["title"]
            )
            history_text = f"《{short_title}》发布记录:\n◯ 尚未发布"

        self._window["-PUBLISH_HISTORY-"].update(history_text)

    def _build_table_data(self, articles=None):
        """构建表格数据"""
        if articles is None:
            articles = self._articles

        return [
            [
                i + 1,
                a["title"],
                a["create_time"],
                a["size"],
                a["status_text"],
            ]
            for i, a in enumerate(articles)
        ]

    def run(self):
        """运行文章管理窗口"""
        self._window = sg.Window(
            "文章管理",
            self._create_layout(),
            size=(1000, 600),
            finalize=True,
            resizable=True,
            element_justification="center",
            icon=self.__get_icon(),
        )
        # 绑定双击事件
        self._window["-TABLE-"].bind("<Double-1>", "_DoubleClick")

        while True:
            event, values = self._window.read()
            if event == sg.WIN_CLOSED:
                break
            elif event == "-TABLE-" and values["-TABLE-"]:
                # 显示选中文章的发布记录
                if values["-TABLE-"]:
                    selected_row = values["-TABLE-"][0]
                    article = self._articles[selected_row]
                    self._update_publish_history(article)
            elif event == "-TABLE-_DoubleClick" and values["-TABLE-"]:
                # 双击事件，获取选中的第一行
                selected_row = values["-TABLE-"][0]
                article = self._articles[selected_row]
                self._view_article(article["path"], article["title"])
            elif event == "-SEARCH_BTN-":
                search_term = values["-SEARCH-"].strip().lower()
                if not search_term:
                    sg.popup(
                        "请输入文章标题（支持模糊搜索）",
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
                else:
                    filtered_articles = [
                        a for a in self._articles if search_term in a["title"].lower()
                    ]
                    filtered_data = self._build_table_data(filtered_articles)
                    self._window["-TABLE-"].update(values=filtered_data)
            elif event == "-REFRESH-":
                self._articles = self._get_articles()
                data = self._build_table_data()
                self._window["-TABLE-"].update(values=data)
            elif event in ["编辑", "预览", "发布", "删除"] and values["-TABLE-"]:
                # 检查是否正在发布中
                if self._publishing and (event == "发布" or event == "删除"):
                    sg.popup(
                        f"正在发布中，无法执行{event}，请稍候...",
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
                    continue

                for selected_row in values["-TABLE-"]:
                    article = self._articles[selected_row]
                    if event == "编辑":
                        self._edit_article(article["path"], article["title"])
                    elif event == "预览":
                        self._view_article(article["path"], article["title"])
                    elif event == "发布":
                        self._handle_publish([article], values)
                    elif event == "删除":
                        # 弹出确认窗口，显示文章标题
                        confirm_message = f"确认删除文章：{article['title']}？"
                        if (
                            sg.popup_yes_no(
                                confirm_message,
                                title="系统提示",
                                icon=self.__get_icon(),
                            )
                            == "Yes"
                        ):
                            self._delete_article(article["path"], article["title"])
                            self._articles = self._get_articles()
                            self._window["-TABLE-"].update(values=self._build_table_data())
            elif event == "-PUBLISH_SELECTED-":
                if values["-TABLE-"]:
                    selected_articles = [self._articles[i] for i in values["-TABLE-"]]
                    self._handle_publish(selected_articles, values)
                else:
                    sg.popup(
                        "请先选择文章，然后再点击批量发布。",
                        non_blocking=True,
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
            elif event == "-BATCH_DELETE-":
                if values["-TABLE-"]:
                    selected_titles = [self._articles[i]["title"] for i in values["-TABLE-"]]
                    confirm_message = "确认删除以下文章？\n" + "\n".join(
                        f"- {title}" for title in selected_titles
                    )
                    if (
                        sg.popup_yes_no(
                            confirm_message,
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
                        == "Yes"
                    ):
                        for selected_row in values["-TABLE-"]:
                            article = self._articles[selected_row]
                            self._delete_article(article["path"], article["title"])
                        self._articles = self._get_articles()
                        self._window["-TABLE-"].update(values=self._build_table_data())
                else:
                    sg.popup(
                        "请先选择文章，然后再点击批量删除。",
                        non_blocking=True,
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
            elif event == "-ADD_CONFIG-":
                appid = values["-APPID-"].strip()
                appsecret = values["-APPSECRET-"].strip()
                author = values["-AUTHOR-"].strip()
                if self._add_temp_credential(appid, appsecret, author):
                    self._window["-CONFIGS-"].update(
                        values=(
                            [f"{c['author']} ({c['appid']})" for c in self._credentials]
                            + [
                                f"[临时]{c['author']} ({c['appid']})"
                                for c in self._temp_credentials
                            ]
                        )
                        or ["无配置"]
                    )
                    self._window["-APPID-"].update("")
                    self._window["-APPSECRET-"].update("")
                    self._window["-AUTHOR-"].update("")
            elif event == "-PUBLISH_COMPLETE-":
                results = values[event]
                # 处理发布结果，更新界面
                self._handle_publish_results(results)

        self._window.close()

    def _handle_publish_results(self, results):
        """处理发布结果"""
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        message = f"文章发布完成！成功: {success_count}/{total_count}"
        if success_count < total_count:
            failed_results = [r for r in results if not r["success"]]
            message += "\n失败的文章:\n" + "\n".join(
                [
                    f"- {r['title']}: {r.get('error', r.get('result', '未知错误'))}"
                    for r in failed_results
                ]
            )

        sg.popup_scrolled(message, title="发布结果", size=(60, 20), icon=self.__get_icon())

        # 重新启用发布按钮
        self._disable_publish_buttons(False)

        # 发布后刷新文章列表以更新状态
        self._articles = self._get_articles()
        data = self._build_table_data()
        self._window["-TABLE-"].update(values=data)

        self._window["-PUBLISH_HISTORY-"].update("发布完成，请选择文章查看发布记录")

    def _publish_articles_background(self, articles, credentials):
        """后台执行发布操作"""

        # 传递所有选中的文章和配置
        all_results = []
        for article in articles:
            if not os.path.exists(article["path"]):
                continue

            with open(article["path"], "r", encoding="utf-8") as file:
                article_content = file.read()
            try:
                title, digest = utils.extract_html(article_content)
            except Exception:
                continue

            article_results = self._publish_article(article_content, title, digest, credentials)
            all_results.extend(article_results)

        return all_results

    def _disable_publish_buttons(self, disabled):
        """禁用/启用发布相关按钮"""
        buttons_to_disable = [
            "-PUBLISH_SELECTED-",  # 发布选中文章按钮
            "-ADD_CONFIG-",  # 添加配置按钮
            "-BATCH_DELETE-",  # 批量删除
        ]

        for button_key in buttons_to_disable:
            self._window[button_key].update(disabled=disabled)

        # 也可以禁用右键菜单中的发布选项
        # 但PySimpleGUI的右键菜单不支持动态禁用，需要其他处理方式
        self._publishing = disabled

    def _handle_publish(self, articles, values):
        """处理发布逻辑，验证配置并执行发布"""
        selected_credentials = []
        selected_indices = values["-CONFIGS-"]

        if selected_indices and (self._credentials or self._temp_credentials):
            # 优化匹配逻辑，直接基于 appid 比较
            for c in self._credentials + self._temp_credentials:
                if (
                    f"{c['author']} ({c['appid']})" in selected_indices
                    or f"[临时]{c['author']} ({c['appid']})" in selected_indices
                ):
                    selected_credentials.append(c)

        if not selected_credentials:
            sg.popup_error(
                "请先选择微信公众号配置或添加临时配置并选择",
                non_blocking=True,
                title="系统提示",
                icon=self.__get_icon(),
            )
            return

        # 禁用发布相关按钮，但保持窗口可关闭
        self._disable_publish_buttons(True)

        # 使用 perform_long_operation 执行发布
        self._window.perform_long_operation(
            lambda: self._publish_articles_background(articles, selected_credentials),
            "-PUBLISH_COMPLETE-",
        )

        # 显示进度提示
        sg.popup_non_blocking(
            "正在后台发布文章，请稍后...\n可关闭界面，但不再收到完成通知 :)",
            title="系统提示",
            icon=self.__get_icon(),
        )

    def __get_icon(self):
        """获取窗口图标"""
        return utils.get_res_path("UI\\icon.ico", os.path.dirname(__file__))


def gui_start():
    """启动文章管理界面"""
    ArticleManager().run()


if __name__ == "__main__":
    gui_start()
