"""语音识别服务
支持国内主流语音识别API：讯飞、百度、腾讯
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional
import httpx
from app.config import get_settings

settings = get_settings()


class TranscriptionService:
    """语音识别服务"""

    def __init__(self):
        self.api_key = settings.SPEECH_API_KEY
        self.api_url = settings.SPEECH_API_URL
        self.speech_provider = settings.SPEECH_PROVIDER  # iflytek / baidu / tencent

    async def transcribe(self, file_path: str) -> Optional[str]:
        """语音识别 - 根据配置的提供商调用相应API"""
        if not self.api_key or not self.api_url:
            # 降级：返回示例文本
            return "这是语音识别的示例文本。请配置真实的语音识别API。\n\n配置方法请查看 DEPLOYMENT.md"

        try:
            if self.speech_provider == "iflytek":
                return await self._transcribe_iflytek(file_path)
            elif self.speech_provider == "baidu":
                return await self._transcribe_baidu(file_path)
            elif self.speech_provider == "tencent":
                return await self._transcribe_tencent(file_path)
            else:
                return await self._transcribe_generic(file_path)
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    async def _transcribe_generic(self, file_path: str) -> Optional[str]:
        """通用语音识别接口"""
        async with httpx.AsyncClient(timeout=60) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": f}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("text", "")

    async def _transcribe_iflytek(self, file_path: str) -> Optional[str]:
        """讯飞语音识别
        文档: https://www.xfyun.cn/doc/asr/ifaas/API.html
        """
        import websockets
        import asyncio

        # 读取音频文件
        with open(file_path, "rb") as f:
            audio_data = f.read()

        # 讯飞API参数
        app_id = settings.IFLYTEK_APP_ID
        api_secret = settings.IFLYTEK_API_SECRET
        api_key = settings.IFLYTEK_API_KEY

        # 构建鉴权URL
        url = "wss://rtasr.xfyun.cn/v1/ws"
        auth_url = self._build_iflytek_auth_url(url, api_key, api_secret)

        # WebSocket连接识别
        async with websockets.connect(auth_url) as ws:
            # 发送音频数据
            await ws.send(json.dumps({
                "common": {"app_id": app_id},
                "parameter": {
                    "language": "zh_cn",
                    "accent": "mandarin",
                    "vad_eos": 3000,
                    "dwa": "wpgs"
                },
                "business": {"aue": "raw", "auf": "audio/L16;rate=16000"},
                "data": {
                    "status": 2,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(audio_data).decode()
                }
            }))

            # 接收结果
            result_text = ""
            async for message in ws:
                data = json.loads(message)
                if data.get("code") == 0:
                    result = data.get("data", {}).get("result", {})
                    text = result.get("ws", [{}])[0].get("cw", [{}])[0].get("w", "")
                    result_text += text

            return result_text if result_text else None

    def _build_iflytek_auth_url(self, url: str, api_key: str, api_secret: str) -> str:
        """构建讯飞鉴权URL"""
        from urllib.parse import urlencode, urlparse
        from wsgiref.handlers import format_date_time
        from datetime import datetime

        parsed = urlparse(url)
        host = parsed.hostname
        path = parsed.path

        # 构建签名
        now = datetime.now()
        date = format_date_time(int(now.timestamp()))

        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode()

        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode()

        return f"{url}?authorization={authorization}&date={date}&host={host}"

    async def _transcribe_baidu(self, file_path: str) -> Optional[str]:
        """百度语音识别
        文档: https://ai.baidu.com/ai-doc/SPEECH/Vk38lxily
        """
        # 获取access_token
        access_token = await self._get_baidu_access_token()

        # 读取音频文件
        with open(file_path, "rb") as f:
            audio_data = f.read()

        # 调用识别API
        url = f"https://vop.baidu.com/server_api?cuid=subtitle_platform&token={access_token}"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={"Content-Type": "audio/wav; rate=16000"},
                content=audio_data
            )
            response.raise_for_status()
            data = response.json()

            if data.get("err_no") == 0:
                return data.get("result", [""])[0]
            else:
                print(f"Baidu API error: {data.get('err_msg')}")
                return None

    async def _get_baidu_access_token(self) -> str:
        """获取百度access_token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={
                    "grant_type": "client_credentials",
                    "client_id": settings.BAIDU_API_KEY,
                    "client_secret": settings.BAIDU_API_SECRET
                }
            )
            data = response.json()
            return data.get("access_token", "")

    async def _transcribe_tencent(self, file_path: str) -> Optional[str]:
        """腾讯语音识别
        文档: https://cloud.tencent.com/document/product/1093/37138
        """
        # 腾讯云API签名和调用需要额外的SDK
        # 这里提供基本框架，实际使用需要安装腾讯云SDK
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.asr.v20190614 import asr_client, models

            # 创建认证对象
            cred = credential.Credential(settings.TENCENT_SECRET_ID, settings.TENCENT_SECRET_KEY)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "asr.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = asr_client.AsrClient(cred, "", clientProfile)

            # 读取音频
            with open(file_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode()

            # 调用识别
            req = models.CreateRecTaskRequest()
            req.EngineModelType = "16k_zh"
            req.ChannelNum = 1
            req.ResTextFormat = 0
            req.SourceType = 1
            req.Data = audio_data
            req.DataLen = len(audio_data)

            resp = client.CreateRecTask(req)
            result = json.loads(resp.to_json_string())

            # 查询结果
            task_id = result["Data"]["TaskId"]
            return await self._poll_tencent_result(client, task_id)

        except ImportError:
            print("Tencent SDK not installed. Run: pip install tencentcloud-sdk-python")
            return None

    async def _poll_tencent_result(self, client, task_id: str, max_retries: int = 30) -> Optional[str]:
        """轮询腾讯识别结果"""
        from tencentcloud.asr.v20190614 import models

        for _ in range(max_retries):
            req = models.DescribeTaskStatusRequest()
            req.TaskId = task_id
            resp = client.DescribeTaskStatus(req)
            result = json.loads(resp.to_json_string())

            status = result["Data"]["Status"]
            if status == 2:  # 识别完成
                return result["Data"]["Result"]
            elif status == 3:  # 识别失败
                print(f"Tencent recognition failed: {result['Data'].get('ErrorMessage')}")
                return None

            await asyncio.sleep(1)

        return None
