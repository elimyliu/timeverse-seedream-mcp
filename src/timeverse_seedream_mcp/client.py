"""
Seedream API 客户端模块

封装火山引擎 Seedream 图片生成 API 的 HTTP 调用。
兼容 OpenAI Images API 格式，使用 httpx 作为异步 HTTP 客户端。
"""

import base64
import os
from io import BytesIO
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from timeverse_seedream_mcp.config import settings


class SeedreamImageResult(BaseModel):
    """单张图片生成结果"""
    b64_json: Optional[str] = None
    url: Optional[str] = None
    revised_prompt: Optional[str] = None
    index: Optional[int] = None


class SeedreamResponse(BaseModel):
    """API 响应模型"""
    created: int
    data: list[SeedreamImageResult]


class SeedreamClient:
    """Seedream API 异步客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
    ):
        self.api_key = api_key or settings.volc_api_key
        self.base_url = base_url or settings.volc_base_url
        self.model = model or settings.volc_model
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "VOLC_API_KEY 未设置。请设置环境变量 VOLC_API_KEY "
                "或在启动时传入 api_key 参数。"
            )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    async def generate(
        self,
        prompt: str,
        size: str = "2K",
        n: int = 1,
        image_urls: Optional[list[str]] = None,
        sequential: Optional[str] = None,
        max_images: Optional[int] = None,
        output_format: str = "png",
        response_format: str = "url",
        watermark: bool = False,
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        extra_body: Optional[dict] = None,
    ) -> SeedreamResponse:
        """
        调用 Seedream 图片生成 API

        Args:
            prompt: 图片描述文本
            size: 输出尺寸 (1K/2K/3K/4K 或自定义如 1024x1024)
            n: 生成图片数量
            image_urls: 参考图片 URL 列表（用于图生图/多图融合）
            sequential: 组图模式 ("auto" 或 "disabled")
            max_images: 组图最大张数
            output_format: 输出格式 (png/jpeg)
            response_format: 返回格式 (url/b64_json)
            watermark: 是否添加水印
            stream: 是否流式输出
            tools: 扩展能力（如联网搜索）
            extra_body: 额外参数

        Returns:
            SeedreamResponse 对象
        """
        body: dict = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": n,
            "output_format": output_format,
            "response_format": response_format,
            "watermark": watermark,
            "stream": stream,
        }

        # 图生图 / 多图融合
        if image_urls:
            body["image"] = image_urls

        # 组图模式
        if sequential:
            body["sequential_image_generation"] = sequential
            if max_images:
                body["sequential_image_generation_options"] = {
                    "max_images": max_images
                }

        # 联网搜索 (5.0 专属)
        if tools:
            body["tools"] = tools

        # 额外参数 (provider 等)
        if extra_body:
            body.update(extra_body)

        response = await self._client.post(
            "/images/generations",
            json=body,
        )
        response.raise_for_status()
        return SeedreamResponse(**response.json())

    async def generate_stream(
        self,
        prompt: str,
        size: str = "2K",
        n: int = 1,
        image_urls: Optional[list[str]] = None,
        output_format: str = "png",
        watermark: bool = False,
    ):
        """
        流式调用 Seedream 图片生成 API

        返回异步生成器，逐块推送 SSE 事件。
        """
        body: dict = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": n,
            "output_format": output_format,
            "watermark": watermark,
            "stream": True,
        }

        if image_urls:
            body["image"] = image_urls

        async with self._client.stream("POST", "/images/generations", json=body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
                if decoded_line.startswith("data: "):
                    yield decoded_line[6:]

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.aclose()
