from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
import requests
from io import BytesIO
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
from dashscope import ImageSynthesis
import os
import mimetypes
import json
import time

from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.config.config import Config


class PublishStatus(Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    DRAFT = "draft"
    SCHEDULED = "scheduled"


@dataclass
class PublishResult:
    publishId: str
    status: PublishStatus
    publishedAt: datetime
    platform: str
    url: Optional[str] = None


class WeixinPublisher:
    BASE_URL = "https://api.weixin.qq.com/cgi-bin"

    def __init__(self, app_id: str, app_secret: str, author: str):
        # 获取配置数据，只能使用确定的配置，微信配置是循环发布的，需要传递
        config = Config.get_instance()

        self.access_token_data = None
        self.app_id = app_id
        self.app_secret = app_secret
        self.author = author
        self.img_api_type = config.img_api_type  # 只有一种模型，统一从配置读取
        self.img_api_key = config.img_api_key
        self.img_api_model = config.img_api_model

    def _ensure_access_token(self):
        # 检查现有token是否有效
        if self.access_token_data and self.access_token_data[
            "expires_at"
        ] > datetime.now() + timedelta(
            minutes=1
        ):  # 预留1分钟余量
            return self.access_token_data["access_token"]

        # 获取新token
        url = f"{self.BASE_URL}/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"  # noqa 501

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in")

            if not access_token:
                print(f"获取access_token失败: {data}")
                return None

            self.access_token_data = {
                "access_token": access_token,
                "expires_in": expires_in,
                "expires_at": datetime.now() + timedelta(seconds=expires_in),
            }
            return access_token
        except requests.exceptions.RequestException as e:
            print(f"获取微信access_token失败: {e}")

        return None  # 获取不到就返回None，失败交给后面的流程处理

    def _upload_draft(self, article, title, digest, media_id):
        token = self._ensure_access_token()
        url = f"{self.BASE_URL}/draft/add?access_token={token}"

        articles = [
            {
                "title": title[:64],  # 标题长度不能超过64
                "author": self.author,
                "digest": digest[:120],
                "content": article,
                "thumb_media_id": media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            },
        ]
        ret = None
        try:
            data = {"articles": articles}

            headers = {"Content-Type": "application/json"}
            json_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            response = requests.post(url, data=json_data, headers=headers)
            response.raise_for_status()
            data = response.json()

            if "errcode" in data and data.get("errcode") != 0:
                print(f"上传草稿失败: {data.get('errmsg')}")
            elif "media_id" not in data:
                print("上传草稿失败: 响应中缺少 media_id")
            else:
                ret = {
                    "media_id": data.get("media_id"),
                }
        except requests.exceptions.RequestException as e:
            print(f"上传微信草稿失败: {e}")

        return ret

    def _generate_img_by_ali(self, prompt, size="1024*1024"):
        image_dir = utils.get_current_dir("image")
        img_url = None
        try:
            rsp = ImageSynthesis.call(
                api_key=self.img_api_key,
                model=self.img_api_model,
                prompt=prompt,
                negative_prompt="低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良",
                n=1,
                size=size,
            )
            if rsp.status_code == HTTPStatus.OK:
                # 实际上只有一张图片，为了节约，不同时生成多张
                for result in rsp.output.results:
                    file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
                    # 拼接绝对路径和文件名
                    file_path = os.path.join(image_dir, file_name)
                    with open(file_path, "wb+") as f:
                        f.write(requests.get(result.url).content)
                img_url = rsp.output.results[0].url
            else:
                print(
                    "sync_call Failed, status_code: %s, code: %s, message: %s"
                    % (rsp.status_code, rsp.code, rsp.message)
                )
        except Exception as e:
            print(f"_generate_img_by_ali调用失败: {e}")

        return img_url

    def generate_img(self, prompt, size="1024*1024"):
        img_url = None
        if self.img_api_type == "ali":
            img_url = self._generate_img_by_ali(prompt, size)
        elif self.img_api_type == "picsum":
            image_dir = utils.get_current_dir("image")
            width_height = size.split("*")
            img_url = utils.download_and_save_image(
                f"https://picsum.photos/{width_height[0]}/{width_height[1]}?random=1",
                image_dir,
            )

        return img_url

    def upload_image(self, image_url):
        if not image_url:
            # 如果图片URL为空，则返回一个默认的图片ID
            return "SwCSRjrdGJNaWioRQUHzgF68BHFkSlb_f5xlTquvsOSA6Yy0ZRjFo0aW9eS3JJu_"

        media_id = None
        try:
            if image_url.startswith(("http://", "https://")):
                # 处理网络图片
                image_response = requests.get(image_url, stream=True)
                image_response.raise_for_status()
                image_buffer = BytesIO(image_response.content)

                # 动态确定 MIME 类型和文件名后缀
                mime_type = image_response.headers.get("Content-Type")
                if not mime_type:
                    mime_type = "image/jpeg"  # 默认值
                file_ext = mimetypes.guess_extension(mime_type)
                file_name = "image" + file_ext if file_ext else "image.jpg"
            else:
                # 处理本地图片
                if not os.path.exists(image_url):
                    print(f"本地图像文件未找到: {image_url}")
                    return None

                with open(image_url, "rb") as f:
                    image_buffer = BytesIO(f.read())

                # 动态确定 MIME 类型和文件名后缀
                mime_type, _ = mimetypes.guess_type(image_url)
                if not mime_type:
                    mime_type = "image/jpeg"  # 默认值
                file_name = os.path.basename(image_url)

            token = self._ensure_access_token()
            url = f"{self.BASE_URL}/material/add_material?access_token={token}&type=image"

            files = {"media": (file_name, image_buffer, mime_type)}
            response = requests.post(url, files=files)
            response.raise_for_status()
            data = response.json()

            if "errcode" in data and data.get("errcode") != 0:
                print(f"上传图片失败: {data.get('errmsg')}")
            elif "media_id" not in data:
                print("上传图片失败: 响应中缺少 media_id")
            else:
                media_id = data.get("media_id"), data.get("url")

        except requests.exceptions.RequestException as e:
            print(f"上传微信图片失败: {e}")

        return media_id

    def add_draft(self, article, title, digest, media_id):
        ret = None
        try:
            # 上传草稿
            draft = self._upload_draft(article, title, digest, media_id)
            if draft is not None:
                ret = PublishResult(
                    publishId=draft["media_id"],
                    status=PublishStatus.DRAFT,
                    publishedAt=datetime.now(),
                    platform="weixin",
                    url=f"https://mp.weixin.qq.com/s/{draft['media_id']}",
                )
        except Exception as e:
            print(f"微信添加草稿失败: {e}")

        return ret

    def publish(self, media_id: str):
        """
        发布草稿箱中的图文素材

        :param media_id: 要发布的草稿的media_id
        :return: 包含发布任务ID的字典
        """
        ret = None
        url = f"{self.BASE_URL}/freepublish/submit"
        params = {"access_token": self._ensure_access_token()}
        data = {"media_id": media_id}

        try:
            response = requests.post(url, params=params, json=data)
            response.raise_for_status()
            result = response.json()

            if "errcode" in result and result.get("errcode") != 0:
                print(f"草稿发布失败: {result.get('errmsg')}")
            elif "publish_id" not in result:
                print("草稿发布失败: 响应中缺少 publish_id")
            else:
                ret = PublishResult(
                    publishId=result.get("publish_id"),
                    status=PublishStatus.PUBLISHED,
                    publishedAt=datetime.now(),
                    platform="weixin",
                    url="",  # 需要通过轮询获取
                )
        except Exception as e:
            print(f"发布草稿文章失败：{e}")

        return ret

    # 轮询获取文章链接
    def poll_article_url(self, publish_id, max_retries=10, interval=2):
        url = f"{self.BASE_URL}/freepublish/get?access_token={self._ensure_access_token()}"
        params = {"publish_id": publish_id}

        for _ in range(max_retries):
            response = requests.post(url, json=params).json()
            if response.get("article_id"):
                return response.get("article_detail")["item"][0]["article_url"]

            time.sleep(interval)

        return None

    # ---------------------以下接口需要微信认证[个人用户不可用]-------------------------
    # 单独发布只能通过绑定到菜单的形式访问到，无法显示到公众号文章列表
    def create_menu(self, article_url):
        ret = None
        menu_data = {
            "button": [
                {
                    "type": "view",
                    "name": "最新文章",
                    "url": article_url,
                }
            ]
        }
        menu_url = f"{self.BASE_URL}/menu/create?access_token={self._ensure_access_token()}"
        try:
            result = requests.post(menu_url, json=menu_data).json()
            if "errcode" in result and result.get("errcode") != 0:
                print(f"创建菜单失败: {result.get('errmsg')}")
            else:
                ret = "创建菜单成功"
        except Exception as e:
            print(f"创建菜单失败，请确认公众号已经认证:{e}")

        return ret

    # 上传图文消息素材【订阅号与服务号认证后均可用】
    def media_uploadnews(self, article, title, digest, media_id):
        ret = None
        data = {
            "articles": [
                {
                    "thumb_media_id": media_id,
                    "author": self.author,
                    "title": title[:64],
                    "content": article,
                    "digest": digest[:120],
                    "show_cover_pic": 1,
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                },
            ]
        }
        url = f"{self.BASE_URL}/media/uploadnews?access_token={self._ensure_access_token()}"

        try:
            result = requests.post(url, json=data).json()
            if "errcode" in result and result.get("errcode") != 0:
                print(f"上次图文消息素材失败: {result.get('errmsg')}")
            elif "media_id" not in result:
                print("上次图文消息素材失败: 响应中缺少 media_id")
            else:
                ret = result.get("media_id")
        except Exception as e:
            print(f"上传图文素材失败，请检查公众号是否已经认证：{e}")

        return ret

    # 根据标签进行群发【订阅号与服务号认证后均可用】
    def message_mass_sendall(self, media_id):
        ret = None
        data = {
            "filter": {
                "is_to_all": True,
            },
            "mpnews": {"media_id": media_id},
            "msgtype": "mpnews",
            "send_ignore_reprint": 1,
        }
        url = f"{self.BASE_URL}/message/mass/sendall?access_token={self._ensure_access_token()}"

        try:
            result = requests.post(url, json=data).json()
            if "errcode" in result and result.get("errcode") != 0:
                print(f"根据标签进行群发: {result.get('errmsg')}")
            else:
                ret = "群发消息成功"
        except Exception as e:
            print(f"群发消息失败：{e}")

        return ret
