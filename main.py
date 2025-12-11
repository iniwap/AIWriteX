# -*- coding: UTF-8 -*-

import multiprocessing
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"

from aiforge import AIForgeEngine  # noqa


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
