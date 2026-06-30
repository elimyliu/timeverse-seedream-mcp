"""
Seedream MCP Server - 工具定义模块

定义所有 MCP Tool，供 AI 助手调用。
基于火山引擎 Seedream 图片生成 API。
"""

from __future__ import annotations

import base64
import json
import os
from io import BytesIO
from typing import Any, Optional

import httpx
from mcp.types import TextContent, ImageContent, EmbeddedResource

from timeverse_seedream_mcp.client import SeedreamClient
from timeverse_seedream_mcp.config import settings


def _format_result(
    data: list[dict],
    revised_prompt: Optional[str] = None,
    save_dir: Optional[str] = None,
) -> list[TextContent | ImageContent]:
    """
    将 API 返回结果格式化为 MCP Content 列表。

    如果 response_format 是 b64_json，返回图片内容。
    如果 response_format 是 url，返回 URL 文本。
    """
    contents: list[TextContent | ImageContent] = []

    if revised_prompt:
        contents.append(TextContent(
            type="text",
            text=f"✨ 优化后的提示词：{revised_prompt}\n",
        ))

    for i, img in enumerate(data):
        if img.get("b64_json"):
            # 返回 Base64 图片
            contents.append(ImageContent(
                type="image",
                data=img["b64_json"],
                mimeType="image/png",
            ))
        elif img.get("url"):
            # 返回 URL
            contents.append(TextContent(
                type="text",
                text=f"🖼️ 图片 {i + 1}: {img['url']}",
            ))
        else:
            contents.append(TextContent(
                type="text",
                text=f"⚠️ 图片 {i + 1}: 无数据返回",
            ))

    return contents


async def handle_text_to_image(
    prompt: str,
    size: str = "2K",
    n: int = 1,
    model: Optional[str] = None,
    output_format: str = "png",
    watermark: bool = False,
    save_to: Optional[str] = None,
) -> list[TextContent | ImageContent]:
    """
    文生图 - 根据文本描述生成图片。

    Args:
        prompt: 图像描述提示词，中英文均可
        size: 输出尺寸。可选: 1K, 2K, 3K, 4K 或自定义如 1920x1080
        n: 生成图片数量 (1-4)
        model: 模型版本，默认 5.0
        output_format: 输出格式 (png/jpeg)
        watermark: 是否添加水印
        save_to: 保存图片到本地目录（可选）
    """
    client = SeedreamClient(model=model or settings.volc_model)

    try:
        # 使用 b64_json 模式以便支持保存和图片展示
        resp = await client.generate(
            prompt=prompt,
            size=size,
            n=n,
            output_format=output_format,
            response_format="b64_json",
            watermark=watermark,
        )

        if not resp.data:
            return [TextContent(type="text", text="❌ 生成失败：API 返回为空")]

        data_list = []
        for item in resp.data:
            d = {"b64_json": item.b64_json, "url": item.url}
            if item.revised_prompt:
                d["revised_prompt"] = item.revised_prompt
            data_list.append(d)

        # 保存到本地（可选）
        if save_to and data_list[0].get("b64_json"):
            os.makedirs(save_to, exist_ok=True)
            for i, img in enumerate(data_list):
                img_data = base64.b64decode(img["b64_json"])
                ext = "png" if output_format == "png" else "jpg"
                filepath = os.path.join(save_to, f"seedream_{i+1}.{ext}")
                with open(filepath, "wb") as f:
                    f.write(img_data)

        revised = data_list[0].get("revised_prompt") if data_list else None
        return _format_result(data_list, revised_prompt=revised)

    except Exception as e:
        return [TextContent(type="text", text=f"❌ 生成失败：{str(e)}")]
    finally:
        await client.close()


async def handle_image_to_image(
    prompt: str,
    image_url: str,
    size: str = "2K",
    model: Optional[str] = None,
    scale: float = 0.5,
    output_format: str = "png",
    watermark: bool = False,
    save_to: Optional[str] = None,
) -> list[TextContent | ImageContent]:
    """
    图生图 - 基于参考图片生成新图片。

    Args:
        prompt: 图像描述提示词，描述对参考图的修改
        image_url: 参考图片 URL
        size: 输出尺寸
        model: 模型版本（需 4.5 或 5.0）
        scale: 文本描述影响程度 (0-1)，越大文本影响越大
        output_format: 输出格式
        watermark: 是否添加水印
        save_to: 保存图片到本地目录（可选）
    """
    client = SeedreamClient(model=model or settings.volc_model)

    try:
        resp = await client.generate(
            prompt=prompt,
            size=size,
            n=1,
            image_urls=[image_url],
            output_format=output_format,
            response_format="b64_json",
            watermark=watermark,
            extra_body={"scale": scale},
        )

        if not resp.data:
            return [TextContent(type="text", text="❌ 生成失败：API 返回为空")]

        data_list = []
        for item in resp.data:
            d = {"b64_json": item.b64_json, "url": item.url}
            if item.revised_prompt:
                d["revised_prompt"] = item.revised_prompt
            data_list.append(d)

        # 保存到本地
        if save_to and data_list[0].get("b64_json"):
            os.makedirs(save_to, exist_ok=True)
            for i, img in enumerate(data_list):
                img_data = base64.b64decode(img["b64_json"])
                ext = "png" if output_format == "png" else "jpg"
                filepath = os.path.join(save_to, f"seedream_img2img_{i+1}.{ext}")
                with open(filepath, "wb") as f:
                    f.write(img_data)

        revised = data_list[0].get("revised_prompt") if data_list else None
        return _format_result(data_list, revised_prompt=revised)

    except Exception as e:
        return [TextContent(type="text", text=f"❌ 图生图失败：{str(e)}")]
    finally:
        await client.close()


async def handle_merge_images(
    prompt: str,
    image_urls: list[str],
    size: str = "2K",
    model: Optional[str] = None,
    output_format: str = "png",
    watermark: bool = False,
    save_to: Optional[str] = None,
) -> list[TextContent | ImageContent]:
    """
    多图融合 - 融合多张图片生成新图片。

    Args:
        prompt: 融合描述，可用「图1」「图2」指代各图片
        image_urls: 参考图片 URL 列表（最多 10 张）
        size: 输出尺寸
        model: 模型版本（需 4.5 或 5.0）
        output_format: 输出格式
        watermark: 是否添加水印
        save_to: 保存图片到本地目录（可选）
    """
    if len(image_urls) > 10:
        return [TextContent(type="text", text="❌ 图片数量不能超过 10 张")]

    client = SeedreamClient(model=model or settings.volc_model)

    try:
        resp = await client.generate(
            prompt=prompt,
            size=size,
            n=1,
            image_urls=image_urls,
            output_format=output_format,
            response_format="b64_json",
            watermark=watermark,
        )

        if not resp.data:
            return [TextContent(type="text", text="❌ 融合失败：API 返回为空")]

        data_list = []
        for item in resp.data:
            d = {"b64_json": item.b64_json, "url": item.url}
            if item.revised_prompt:
                d["revised_prompt"] = item.revised_prompt
            data_list.append(d)

        # 保存到本地
        if save_to and data_list[0].get("b64_json"):
            os.makedirs(save_to, exist_ok=True)
            for i, img in enumerate(data_list):
                img_data = base64.b64decode(img["b64_json"])
                ext = "png" if output_format == "png" else "jpg"
                filepath = os.path.join(save_to, f"seedream_merge_{i+1}.{ext}")
                with open(filepath, "wb") as f:
                    f.write(img_data)

        revised = data_list[0].get("revised_prompt") if data_list else None
        return _format_result(data_list, revised_prompt=revised)

    except Exception as e:
        return [TextContent(type="text", text=f"❌ 多图融合失败：{str(e)}")]
    finally:
        await client.close()


async def handle_generate_sequence(
    prompt: str,
    max_images: int = 4,
    size: str = "2K",
    model: Optional[str] = None,
    output_format: str = "png",
    watermark: bool = False,
    save_to: Optional[str] = None,
) -> list[TextContent | ImageContent]:
    """
    组图生成 - 根据文本描述生成一组连续图片。

    Args:
        prompt: 图像描述提示词，描述组图的主题
        max_images: 生成图片数量 (1-15)
        size: 输出尺寸
        model: 模型版本（需 4.5 或 5.0）
        output_format: 输出格式
        watermark: 是否添加水印
        save_to: 保存图片到本地目录（可选）
    """
    client = SeedreamClient(model=model or settings.volc_model)

    try:
        resp = await client.generate(
            prompt=prompt,
            size=size,
            n=1,
            sequential="auto",
            max_images=max_images,
            output_format=output_format,
            response_format="b64_json",
            watermark=watermark,
        )

        if not resp.data:
            return [TextContent(type="text", text="❌ 组图生成失败：API 返回为空")]

        data_list = []
        for item in resp.data:
            d = {"b64_json": item.b64_json, "url": item.url, "index": item.index}
            if item.revised_prompt:
                d["revised_prompt"] = item.revised_prompt
            data_list.append(d)

        # 保存到本地
        if save_to:
            os.makedirs(save_to, exist_ok=True)
            for i, img in enumerate(data_list):
                if img.get("b64_json"):
                    img_data = base64.b64decode(img["b64_json"])
                    ext = "png" if output_format == "png" else "jpg"
                    idx = img.get("index", i + 1)
                    filepath = os.path.join(save_to, f"seedream_seq_{idx}.{ext}")
                    with open(filepath, "wb") as f:
                        f.write(img_data)

        revised = data_list[0].get("revised_prompt") if data_list else None
        return _format_result(data_list, revised_prompt=revised)

    except Exception as e:
        return [TextContent(type="text", text=f"❌ 组图生成失败：{str(e)}")]
    finally:
        await client.close()


async def handle_web_search_generate(
    prompt: str,
    size: str = "2K",
    model: Optional[str] = None,
    output_format: str = "png",
    watermark: bool = False,
    save_to: Optional[str] = None,
) -> list[TextContent | ImageContent]:
    """
    联网搜索 + 文生图 - 结合实时信息生成图片（仅 5.0 模型）。

    Args:
        prompt: 图像描述提示词，可包含对实时信息的要求
        size: 输出尺寸
        model: 模型版本（需 5.0）
        output_format: 输出格式
        watermark: 是否添加水印
        save_to: 保存图片到本地目录（可选）
    """
    client = SeedreamClient(model=model or "doubao-seedream-5-0-260128")

    # 联网搜索工具定义
    web_search_tool = {
        "type": "web_search",
        "web_search": {
            "search_mode": "auto",
            "search_scope": "interNet",
            "enable_enhancement": True,
        },
    }

    try:
        resp = await client.generate(
            prompt=prompt,
            size=size,
            n=1,
            output_format=output_format,
            response_format="b64_json",
            watermark=watermark,
            tools=[web_search_tool],
        )

        if not resp.data:
            return [TextContent(type="text", text="❌ 生成失败：API 返回为空")]

        data_list = []
        for item in resp.data:
            d = {"b64_json": item.b64_json, "url": item.url}
            if item.revised_prompt:
                d["revised_prompt"] = item.revised_prompt
            data_list.append(d)

        # 保存到本地
        if save_to and data_list[0].get("b64_json"):
            os.makedirs(save_to, exist_ok=True)
            for i, img in enumerate(data_list):
                img_data = base64.b64decode(img["b64_json"])
                ext = "png" if output_format == "png" else "jpg"
                filepath = os.path.join(save_to, f"seedream_web_{i+1}.{ext}")
                with open(filepath, "wb") as f:
                    f.write(img_data)

        revised = data_list[0].get("revised_prompt") if data_list else None
        return _format_result(data_list, revised_prompt=revised)

    except Exception as e:
        return [TextContent(type="text", text=f"❌ 联网搜索生图失败：{str(e)}")]
    finally:
        await client.close()


async def handle_list_models() -> list[TextContent]:
    """列出可用的 Seedream 模型版本"""
    models = settings.available_models
    lines = ["**📋 可用模型列表：**\n"]
    for version, model_id in models.items():
        lines.append(f"- **v{version}**: `{model_id}`")
    lines.append("\n💡 提示：5.0 支持联网搜索，4.5 和 5.0 支持图生图和组图")
    return [TextContent(type="text", text="\n".join(lines))]
