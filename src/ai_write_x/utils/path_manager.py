import os
import glob
import platform
from pathlib import Path
from src.ai_write_x.utils import utils


class PathManager:
    """跨平台路径管理器，确保所有写入操作使用正确的可写目录"""

    @staticmethod
    def get_app_data_dir():
        """获取应用数据目录"""
        # 开发模式：使用项目根目录
        if not utils.get_is_release_ver():
            # 从当前文件位置回到项目根目录
            return Path(__file__).parent.parent.parent.parent

        # 发布模式：使用系统用户数据目录
        if platform.system() == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/AIWriteX"
        elif platform.system() == "Windows":
            return Path(os.environ.get("APPDATA", "")) / "AIWriteX"
        else:  # Linux
            return Path.home() / ".config/AIWriteX"

    @staticmethod
    def get_config_dir():
        """获取配置文件目录"""
        if not utils.get_is_release_ver():
            # 开发模式：使用源码目录
            return Path(__file__).parent.parent / "config"
        else:
            # 发布模式：使用用户数据目录
            config_dir = PathManager.get_app_data_dir() / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir

    @staticmethod
    def get_article_dir():
        """获取文章目录"""
        article_dir = PathManager.get_app_data_dir() / "output/article"
        article_dir.mkdir(parents=True, exist_ok=True)
        return article_dir

    @staticmethod
    def get_template_dir():
        """获取模板目录 - 始终返回用户可写目录"""
        if not utils.get_is_release_ver():
            # 开发模式：使用项目目录
            return PathManager.get_app_data_dir() / "knowledge/templates"
        else:
            # 发布模式：使用用户数据目录
            template_dir = PathManager.get_app_data_dir() / "templates"
            template_dir.mkdir(parents=True, exist_ok=True)

            # 首次运行时，从资源目录复制默认模板到用户目录
            res_template_dir = utils.get_res_path("templates")
            template_files = glob.glob(os.path.join(template_dir, "*", "*.html"))
            if os.path.exists(res_template_dir) and not template_files:
                import shutil

                shutil.copytree(res_template_dir, template_dir, dirs_exist_ok=True)

            return template_dir

    @staticmethod
    def get_image_dir():
        """获取图片目录"""
        image_dir = PathManager.get_app_data_dir() / "image"
        image_dir.mkdir(parents=True, exist_ok=True)
        return image_dir

    @staticmethod
    def get_log_dir():
        """获取日志目录"""
        log_dir = PathManager.get_app_data_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @staticmethod
    def get_temp_dir():
        """获取临时目录路径"""
        temp_dir = PathManager.get_app_data_dir() / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    @staticmethod
    def get_config_path(file_name="config.yaml"):
        """获取配置文件的完整路径"""
        return PathManager.get_config_dir() / file_name

    @staticmethod
    def ensure_directory_exists(path):
        """确保目录存在，如果不存在则创建"""
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_writable(path):
        """检查路径是否可写"""
        try:
            test_file = Path(path) / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            return False

    @staticmethod
    def get_all_categories(default_template_categories):
        """动态获取所有分类文件夹名称"""
        template_dir = str(PathManager.get_template_dir())
        categories = []
        excluded_dirs = {"components", "__pycache__", ".git"}

        # 添加默认分类
        default_categories = list(default_template_categories.values())
        categories.extend(default_categories)

        # 扫描实际存在的文件夹
        if os.path.exists(template_dir):
            for item in os.listdir(template_dir):
                item_path = os.path.join(template_dir, item)
                if (
                    os.path.isdir(item_path)
                    and item not in categories
                    and item not in excluded_dirs
                ):
                    categories.append(item)

        return sorted(categories)

    @staticmethod
    def get_templates_by_category(category):
        """获取指定分类下的模板列表"""
        if not category or category == "随机分类":
            return []

        template_dir = str(PathManager.get_template_dir())
        category_path = os.path.join(template_dir, category)

        if not os.path.exists(category_path):
            return []

        template_files = glob.glob(os.path.join(category_path, "*.html"))
        template_names = [os.path.splitext(os.path.basename(f))[0] for f in template_files]
        return sorted(template_names)
