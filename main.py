#!/usr/bin/python
# -*- coding: UTF-8 -*-

import multiprocessing
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"

from aiforge import AIForgeEngine  # noqa

# 帮助 PyInstaller 检测依赖 (永远不会执行)
if False:
    import fastapi  # noqa
    import uvicorn  # noqa
    import webview  # noqa
    import jinja2  # noqa
    import pystray  # noqa
    import yaml  # noqa
    import tomlkit  # noqa
    import peewee  # noqa
    from playhouse.sqlite_ext import SqliteExtDatabase  # noqa
    from src.ai_write_x.web import webview_gui  # noqa
    from src.ai_write_x.web import app  # noqa
    from src.ai_write_x.config import config  # noqa
    from src.ai_write_x import crew_main  # noqa
    import bs4  # noqa
    import requests  # noqa
    from PIL import Image  # noqa
    import markdown  # noqa
    from crewai import Agent, Crew, Process, Task  # noqa
    from crewai.project import CrewBase, agent, crew, task  # noqa
    import chromadb  # noqa
    import onnxruntime  # noqa
    from rich.console import Console  # noqa


def run():
    """启动GUI应用程序"""
    try:
        from src.ai_write_x.license import check_license_and_start

        check_license_and_start()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        raise


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)

    if AIForgeEngine.handle_sandbox_subprocess(
        globals_dict=globals().copy(), sys_path=sys.path.copy()
    ):
        sys.exit(0)
    else:
        run()
