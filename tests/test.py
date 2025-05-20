# test.py

import sys
import os

# 获取当前文件（b.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到项目根目录（即 A 和 B 的父目录）
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径
sys.path.append(project_root)

from src.ai_auto_wxgzh.utils import log  # noqa 402
from src.ai_auto_wxgzh.utils import utils  # noqa 402
from src.ai_auto_wxgzh.tools.wx_publisher import WeixinPublisher  # noqa 402
from src.ai_auto_wxgzh.config.config import Config  # noqa 402

article = """"""


def pub2wx(article):
    config = Config.get_instance()
    if not config.load_config():
        log.print_log("加载配置失败，请检查是否有配置！")
        return
    elif not config.validate_config():
        log.print_log(f"配置填写有错误：{config.error_message}")
        return

    try:
        title, digest = utils.extract_html(article)
    except Exception as e:
        return f"从文章中提取标题、摘要信息出错: {e}", article
    if title is None:
        return "无法提取文章标题，请检查文章是否成功生成？", article

    publisher = WeixinPublisher(
        config.wechat_credentials[0]["appid"],
        config.wechat_credentials[0]["appsecret"],
        config.wechat_credentials[0]["author"],
    )

    image_url = publisher.generate_img(
        "主题：" + title.split("|")[-1] + "，内容：" + digest,
        "900*384",
    )

    if image_url is None:
        log.print_log("生成图片出错，使用默认图片")

    # 封面图片
    media_id, _, err_msg = publisher.upload_image(image_url)
    if media_id is None:
        return f"封面{err_msg}，无法发布文章", article

    # 这里需要将文章中的图片url替换为上传到微信返回的图片url
    try:
        image_urls = utils.extract_image_urls(article)
        for image_url in image_urls:
            local_filename = utils.download_and_save_image(
                image_url,
                utils.get_current_dir("image"),
            )
            if local_filename:
                _, url, _ = publisher.upload_image(local_filename)
                article = article.replace(image_url, url)
    except Exception as e:
        log.print_log(f"上传配图出错，影响阅读，可继续发布文章:{e}")

    add_draft_result, err_msg = publisher.add_draft(article, title, digest, media_id)
    if add_draft_result is None:
        # 添加草稿失败，不再继续执行
        return f"{err_msg}，无法发布文章", article

    publish_result, err_msg = publisher.publish(add_draft_result.publishId)
    if publish_result is None:
        return f"{err_msg}，无法继续发布文章", article

    article_url = publisher.poll_article_url(publish_result.publishId)
    if article_url is not None:
        # 该接口需要认证，将文章添加到菜单中去，用户可以通过菜单“最新文章”获取到
        ret = publisher.create_menu(article_url)
        if not ret:
            log.print_log(f"{ret}（公众号未认证，发布已成功）")
    else:
        log.print_log("无法获取到文章URL，无法创建菜单（可忽略，发布已成功）")

    # 只有下面执行成功，文章才会显示到公众号列表，否则只能通过后台复制链接分享访问
    # 通过群发使得文章显示到公众号列表 ——> 该接口需要认证
    ret, media_id = publisher.media_uploadnews(article, title, digest, media_id)
    if media_id is None:
        return f"{ret}，无法显示到公众号文章列表（公众号未认证，发布已成功）", article

    ret = publisher.message_mass_sendall(media_id)
    if ret is not None:
        return (
            f"{ret}，无法显示到公众号文章列表（公众号未认证，发布已成功）",
            article,
        )

    return "成功发布文章到微信公众号", article


# 测试直接发布文章
# log.print_log(pub2wx())
log.print_log(utils.decompress_html(article))
# log.print_log(utils.extract_html(article))
