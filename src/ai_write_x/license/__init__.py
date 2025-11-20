"""
授权模块接口层
此模块在开源版本中为空实现,在商业版本中包含实际授权逻辑
"""


def check_license_and_start():
    """
    检查授权并启动应用

    开源版本:直接启动应用
    商业版本:验证授权后启动

    Returns:
        bool: 是否允许启动
    """
    # 开源版本的默认实现
    from src.ai_write_x.web.webview_gui import gui_start

    gui_start()
    return True


def is_license_enabled():
    """
    检查是否启用授权系统

    Returns:
        bool: 开源版本返回 False,商业版本返回 True
    """
    return False
