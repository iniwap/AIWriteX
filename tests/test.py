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

article = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>百度热点|新冠病毒抬头？钟南山发声</title></head><body><div><section style="background:linear-gradient(135deg,#E57373,#FF5252);color:white;padding:10px 20px;border-radius:0 0 30px 30px;margin-bottom:25px;overflow:hidden;"><h1 style="margin:15px 0 15px 0;font-size:30px;font-weight:900;line-height:1.2;">新冠病毒抬头？钟南山最新发声</h1><div style="display:flex;align-items:center;margin-bottom:15px;"><span style="display:inline-block;font-size:14px;font-weight:600;background-color:rgba(255,255,255,0.2);padding:4px 12px;border-radius:20px;">百度热点</span><span style="display:inline-block;width:4px;height:4px;border-radius:50%;background-color:white;margin:0 8px;"></span><span style="font-size:14px;opacity:0.9;">疫情最新</span></div><p style="margin:0;font-size:16px;line-height:1.6;opacity:0.9;">中国疾控中心最新数据显示新冠阳性率明显上升，钟南山院士就当前疫情形势发表重要看法。</p><div style="margin-top:0px;"><svg width="100%" height="40" viewBox="0 0 320 40" style="overflow:visible;"><path d="M0,20 Q80,40 160,20 T320,20" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="2"/><circle cx="0" cy="0" r="4" fill="white" opacity="0.3"><animateMotion path="M0,20 Q80,40 160,20 T320,20" dur="3s" repeatCount="indefinite" calcMode="linear"/></circle></svg></div><div style="margin-top:-180px;margin-left:auto;margin-right:-40px;width:150px;height:150px;background-color:rgba(255,255,255,0.1);border-radius:50%;"></div><div style="margin-top:-80px;margin-left:-80px;width:100px;height:100px;background-color:rgba(255,255,255,0.1);border-radius:50%;"></div></section><section style="padding:0 0;margin-bottom:0px;"><p style="font-size:17px;line-height:1.7;color:#333;margin:0 0 15px 0;text-align:justify;">最近监测数据显示，中国新冠感染率呈现上升趋势。中国工程院院士钟南山5月19日在广州接受采访时表示，当前疫情"整体上可防可控，不必恐慌"，但65岁以上及有基础病患者等高危人群仍存在一定风险。</p><svg width="100%" height="30" viewBox="0 0 300 30" style="margin:20px 0;"><g fill="#E57373"><path d="M15,15 L30,15 M45,15 L60,15 M75,15 L90,15 M105,15 L120,15 M135,15 L150,15 M165,15 L180,15 M195,15 L210,15 M225,15 L240,15 M255,15 L270,15 M285,15 L300,15" stroke="#E57373" stroke-width="2"></path><circle cx="15" cy="15" r="4"><animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" /></circle><circle cx="150" cy="15" r="4"><animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" begin="0.5s" /></circle><circle cx="285" cy="15" r="4"><animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" begin="1s" /></circle></g></svg></section><section style="margin:0 0 25px;background-color:white;border-radius:15px;overflow:hidden;box-shadow:0 5px 15px rgba(0,0,0,0.05);"><div style="padding:15px 20px 5px;"><h2 style="margin:0 0 20px 0;font-size:24px;font-weight:800;color:#333;padding-left:15px;line-height:1.3;"><span style="display:inline-block;margin-left:-15px;width:5px;height:100%;background-color:#E57373;border-radius:3px;"></span>疫情现状分析</h2><p style="font-size:16px;line-height:1.7;color:#333;margin:0 0 0 0;text-align:justify;">据中国疾控中心5月8日发布的监测数据显示，在4月14日至5月4日期间：</p></div><div style="width:100%;height:200px;margin-bottom:20px;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end;"><img src="http://mmbiz.qpic.cn/mmbiz_jpg/oOYVQHjiaEmx7DPwgjr7UYrzUZ9KLJKiaBQSk4hj27oYLyhyuQVvPh1jmY9MgAF9iaWuCrXGBxY11A3U35lqhJllg/0?wx_fmt=jpeg" alt="背景图片" style="width:100%;height:100%;object-fit:cover;display:block;"><div style="margin-top:-50px;padding:0 15px 5px 15px;background:linear-gradient(to bottom,rgba(0,0,0,0),rgba(0,0,0,0.3));"><span style="color:white;font-size:14px;font-weight:500;text-shadow:0 1px 2px rgba(0,0,0,0.5);">医院发热门诊</span></div></div><div style="padding:0 20px 25px;"><p style="font-size:16px;line-height:1.7;color:#333;margin:0 0 15px 0;text-align:justify;"><span style="font-weight:700;color:#E57373;">•</span> 门急诊流感样病例中，新冠阳性率从7.5%上升至16.2%</p><p style="font-size:16px;line-height:1.7;color:#333;margin:0 0 15px 0;text-align:justify;"><span style="font-weight:700;color:#E57373;">•</span> 住院病例中，新冠阳性率从3.3%上升至6.3%</p><p style="font-size:16px;line-height:1.7;color:#333;margin:0;text-align:justify;"><span style="font-weight:700;color:#E57373;">•</span> 新型冠状病毒已成为门急诊流感样病例就诊量的首位病原体</p></div></section><section style="margin:0 0 15px;"><div style="display:flex;flex-direction:column;gap:10px;"><div style="display:flex;align-items:center;gap:10px;"><div style="width:40px;height:40px;background-color:#FF5252;color:white;display:flex;justify-content:center;align-items:center;border-radius:50%;font-weight:700;font-size:18px;">1</div><div style="flex:1;background-color:white;padding:15px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.05);"><p style="margin:0;font-size:15px;line-height:1.5;color:#555;">当前XBB系列变异株仍为主要流行毒株，病毒变异未导致致病性显著增强</p></div></div><div style="display:flex;align-items:center;gap:10px;"><div style="width:40px;height:40px;background-color:#FF5252;color:white;display:flex;justify-content:center;align-items:center;border-radius:50%;font-weight:700;font-size:18px;">2</div><div style="flex:1;background-color:white;padding:15px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.05);"><p style="margin:0;font-size:15px;line-height:1.5;color:#555;">发热门诊就诊量较上月增长约30%，需警惕医疗资源挤兑风险</p></div></div></div><svg width="100%" height="40" viewBox="0 0 300 40" style="margin-top:15px;"><path d="M150,0 L150,40" stroke="#F5F5F5" stroke-width="2" stroke-dasharray="3,3"></path><g transform="translate(150,20)"><path d="M-10,-10 L0,0 L10,-10 M-10,10 L0,0 L10,10" stroke="#E57373" stroke-width="2" fill="none"></path></g></svg></section><section style="margin:0 0 25px;background-color:#FFEBEE;border-radius:15px;padding:25px 20px;overflow:hidden;"><h2 style="margin:0 0 15px 0;font-size:24px;font-weight:800;color:#333;line-height:1.3;padding:0px 0px 0 0px;">钟南山核心观点</h2><p style="font-size:16px;line-height:1.7;color:#333;margin:0 0 15px 0;text-align:justify;">中国工程院院士钟南山就当前疫情形势提出了重要观点：</p><div style="margin-top:-170px;margin-left:auto;margin-right:-80px;width:150px;height:150px;background-color:rgba(229,115,115,0.1);border-radius:50%;"></div><div style="display:flex;gap:15px;margin:20px 0;"><div style="flex:1;height:4px;background-color:#E57373;border-radius:2px;"></div><div style="flex:2;height:4px;background-color:#EF9A9A;border-radius:2px;"></div><div style="flex:1;height:4px;background-color:#FFCDD2;border-radius:2px;"></div></div><p style="font-size:16px;line-height:1.7;color:#333;margin:0;text-align:justify;">• 当前疫情"整体上可防可控，不必恐慌"<br>• 65岁以上及有基础病患者等高危人群仍存在一定风险<br>• 建议感染后48小时内尽快服用特效药，如奈玛特韦等<br>• 预计本轮疫情将在6月底前结束</p><div style="margin-top:-60px;margin-left:-30px;width:80px;height:80px;background-color:rgba(229,115,115,0.1);border-radius:50%;"></div></section><section style="margin:0 0 25px;background-color:white;border-radius:15px;box-shadow:0 5px 15px rgba(0,0,0,0.05);"><div style="padding:25px 20px;"><h2 style="margin:0 0 20px 0;font-size:24px;font-weight:800;color:#333;line-height:1.3;">防控建议升级</h2><p style="font-size:16px;line-height:1.7;color:#333;margin:0 0 20px 0;text-align:justify;">针对当前疫情形势，专家提出以下防控建议：</p><div style="display:flex;flex-direction:column;gap:10px;"><div style="display:flex;gap:10px;align-items:center;"><div style="width:36px;height:36px;flex-shrink:0;border-radius:50%;background-color:#FFEBEE;display:flex;justify-content:center;align-items:center;"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10,3 L17,7 L17,13 L10,17 L3,13 L3,7 Z" stroke="#E57373" stroke-width="1.5" fill="none"></path></svg></div><p style="margin:0;font-size:15px;line-height:1.5;color:#555;">强调重点场所佩戴口罩的必要性</p></div><div style="display:flex;gap:10px;align-items:center;"><div style="width:36px;height:36px;flex-shrink:0;border-radius:50%;background-color:#FFEBEE;display:flex;justify-content:center;align-items:center;"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5,10 A5,5 0 0,1 15,10 A5,5 0 0,1 5,10 Z" stroke="#E57373" stroke-width="1.5" fill="none"></path></svg></div><p style="margin:0;font-size:15px;line-height:1.5;color:#555;">养老院、学校等重点场所加强监测</p></div></div><div style="margin:20px 0;padding:15px;background-color:#FFEBEE;border-radius:10px;border-left:4px solid #E57373;"><p style="margin:0;font-size:15px;line-height:1.6;color:#333;font-style:italic;">钟南山院士特别强调：疫情可能在6月中旬达到高峰，但重症率较上一波有所下降，建议维持现有防控力度至疫情回落。</p></div><p style="font-size:16px;line-height:1.7;color:#333;margin:0;text-align:justify;">呼吁高危人群及时接种加强针疫苗，出现发热症状应居家自测抗原，完善分级诊疗体系，确保抗病毒药物充足供应。</p></div></section><section style="margin:0 0 35px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 20px;"><svg viewBox="0 0 100 100" width="100%" height="100%"><defs><linearGradient id="catGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#FF5252;stop-opacity:1" /><stop offset="100%" style="stop-color:#E57373;stop-opacity:1" /></linearGradient><path id="breathPath" d="M0 0 Q0 2 0 0" visibility="hidden"/></defs><rect x="20" y="75" width="60" height="15" rx="2" fill="#FF5252" /><rect x="25" y="50" width="50" height="15" rx="2" fill="#FF5252" /><rect x="30" y="25" width="40" height="15" rx="2" fill="#FF5252" /><rect x="30" y="65" width="5" height="10" fill="#D32F2F" /><rect x="65" y="65" width="5" height="10" fill="#D32F2F" /><rect x="35" y="40" width="5" height="10" fill="#D32F2F" /><rect x="60" y="40" width="5" height="10" fill="#D32F2F" /><g transform="translate(50 30)"><circle cx="0" cy="0" r="8" fill="#FFEBEE"><animateMotion dur="2s" repeatCount="indefinite" path="M0 0 Q0 2 0 0" rotate="auto" calcMode="spline" keyPoints="0;0.5;1" keyTimes="0;0.5;1" keySplines="0.5 0 0.5 1;0.5 0 0.5 1" /></circle></g><path d="M45 26 L42 20 L46 25 Z" fill="#FFEBEE"/><path d="M55 26 L58 20 L54 25 Z" fill="#FFEBEE"/></svg></div><h2 style="margin:0 0 15px 0;font-size:24px;font-weight:800;color:#333;line-height:1.3;">专家提醒</h2><p style="font-size:16px;line-height:1.7;color:#333;margin:0 0 20px 0;text-align:justify;">虽然当前疫情可控，但仍需注意：避免聚集性活动，保持良好卫生习惯，关注官方发布的疫情动态。科学防控，理性应对，我们终将战胜疫情！</p><div style="padding:20px;background-color:#FFEBEE;border-radius:15px;margin-bottom:20px;"><p style="margin:0;font-size:17px;line-height:1.7;color:#333;font-weight:500;text-align:center;">钟南山院士表示：现有疫苗仍能提供有效保护，65岁以上人群应及时接种加强针疫苗。</p></div><p style="font-size:16px;line-height:1.7;color:#666;margin:0;text-align:center;font-style:italic;">科学精准落实防控措施，既保护自己，也保护他人，共同维护社会公共卫生安全。</p></section></div></body></html>"""


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
