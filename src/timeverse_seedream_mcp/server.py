"""
Seedream MCP Server - MCP 服务器主模块

注册所有 Seedream 图片生成工具，提供 MCP 协议接口。
"""

from __future__ import annotations

from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.lowlevel.server import McpError
from mcp.server.models import InitializationOptions

from timeverse_seedream_mcp.config import settings
from timeverse_seedream_mcp.tools import (
    handle_text_to_image,
    handle_image_to_image,
    handle_merge_images,
    handle_generate_sequence,
    handle_web_search_generate,
    handle_list_models,
)

# 创建 MCP Server 实例
server = Server(settings.server_name)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """注册所有可用的 Seedream 工具"""
    return [
        types.Tool(
            name="seedream_text_to_image",
            description="""文生图：根据文本描述生成图片。

使用 Seedream 模型（默认 5.0）根据文本提示词生成高质量图片。
支持 1K/2K/3K/4K 等多种分辨率，可一次生成多张图片。

示例：
- "一只可爱的柴犬在樱花树下睡觉，宫崎骏动画风格"
- "未来城市夜景，赛博朋克风格，霓虹灯闪烁，4K画质"
- "水墨画风格的山水，远山如黛，近水含烟"

注意：5.0 和 4.0 版本支持 n>1（多张），4.5 仅支持 n=1。
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图像描述提示词，中英文均可。建议不超过 300 个汉字或 600 个英文单词",
                    },
                    "size": {
                        "type": "string",
                        "description": "输出尺寸。可选: 1K, 2K, 3K, 4K 或自定义如 1920x1080",
                        "default": "2K",
                    },
                    "n": {
                        "type": "integer",
                        "description": "生成图片数量 (1-4)。注意: 4.5 模型仅支持 1 张",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 4,
                    },
                    "model": {
                        "type": "string",
                        "description": "模型版本。可选: doubao-seedream-5-0-260128, doubao-seedream-4-5-251128, doubao-seedream-4-0-250828",
                        "default": "doubao-seedream-5-0-260128",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式: png (默认, 仅5.0支持) 或 jpeg",
                        "default": "png",
                        "enum": ["png", "jpeg"],
                    },
                    "response_format": {
                        "type": "string",
                        "description": "返回格式: url（返回图片链接）或 b64_json（返回base64编码图片数据）",
                        "default": "url",
                        "enum": ["url", "b64_json"],
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "是否添加水印",
                        "default": False,
                    },
                    "save_to": {
                        "type": "string",
                        "description": "保存图片到本地目录路径（b64_json 模式必填）。如: /Users/xxx/images",
                    },
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="seedream_image_to_image",
            description="""图生图：基于参考图片生成新图片。

提供一张参考图片 URL，结合文本描述生成新的图片。
支持 4.5 和 5.0 模型。

示例：
- prompt: "把这张照片改成油画风格"
- prompt: "给这张图片加上星空背景"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图像描述提示词，描述对参考图的修改",
                    },
                    "image_url": {
                        "type": "string",
                        "description": "参考图片 URL（需可公开访问的图片地址）",
                    },
                    "size": {
                        "type": "string",
                        "description": "输出尺寸",
                        "default": "2K",
                    },
                    "model": {
                        "type": "string",
                        "description": "模型版本（需 4.5 或 5.0）",
                        "default": "doubao-seedream-5-0-260128",
                    },
                    "scale": {
                        "type": "number",
                        "description": "文本描述影响程度 (0-1)，越大文本影响越大",
                        "default": 0.5,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式",
                        "default": "png",
                        "enum": ["png", "jpeg"],
                    },
                    "response_format": {
                        "type": "string",
                        "description": "返回格式: url（返回图片链接）或 b64_json（返回base64编码图片数据）",
                        "default": "url",
                        "enum": ["url", "b64_json"],
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "是否添加水印",
                        "default": False,
                    },
                    "save_to": {
                        "type": "string",
                        "description": "保存图片到本地目录路径（b64_json 模式必填）",
                    },
                },
                "required": ["prompt", "image_url"],
            },
        ),
        types.Tool(
            name="seedream_merge_images",
            description="""多图融合：融合多张图片生成新图片。

提供多张参考图片 URL，结合文本描述将它们融合成一张新图片。
最多支持 10 张图片，可在提示词中用「图1」「图2」等指代各图片。

示例：
- prompt: "把图1的人物放到图2的背景中"
- prompt: "融合图1和图2的风格，生成一张新年贺卡"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "融合描述提示词。可用「图1」「图2」等指代各图片",
                    },
                    "image_urls": {
                        "type": "array",
                        "items": {"type": "string", "description": "图片 URL"},
                        "description": "参考图片 URL 列表（最多 10 张）",
                        "maxItems": 10,
                    },
                    "size": {
                        "type": "string",
                        "description": "输出尺寸",
                        "default": "2K",
                    },
                    "model": {
                        "type": "string",
                        "description": "模型版本（需 4.5 或 5.0）",
                        "default": "doubao-seedream-5-0-260128",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式",
                        "default": "png",
                        "enum": ["png", "jpeg"],
                    },
                    "response_format": {
                        "type": "string",
                        "description": "返回格式: url（返回图片链接）或 b64_json（返回base64编码图片数据）",
                        "default": "url",
                        "enum": ["url", "b64_json"],
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "是否添加水印",
                        "default": False,
                    },
                    "save_to": {
                        "type": "string",
                        "description": "保存图片到本地目录路径（b64_json 模式必填）",
                    },
                },
                "required": ["prompt", "image_urls"],
            },
        ),
        types.Tool(
            name="seedream_generate_sequence",
            description="""组图生成：根据文本描述生成一组连续图片。

适用于需要生成多张连续画面的场景，如故事板、漫画分镜等。
支持 4.5 和 5.0 模型，每批最多 15 张。

示例：
- prompt: "一只小猫咪从出生到长大的四个阶段"
- prompt: "四季变换的同一片森林，春、夏、秋、冬"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图像描述提示词，描述组图的主题和内容",
                    },
                    "max_images": {
                        "type": "integer",
                        "description": "生成图片数量 (1-15)",
                        "default": 4,
                        "minimum": 1,
                        "maximum": 15,
                    },
                    "size": {
                        "type": "string",
                        "description": "输出尺寸",
                        "default": "2K",
                    },
                    "model": {
                        "type": "string",
                        "description": "模型版本（需 4.5 或 5.0）",
                        "default": "doubao-seedream-5-0-260128",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式",
                        "default": "png",
                        "enum": ["png", "jpeg"],
                    },
                    "response_format": {
                        "type": "string",
                        "description": "返回格式: url（返回图片链接）或 b64_json（返回base64编码图片数据）",
                        "default": "url",
                        "enum": ["url", "b64_json"],
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "是否添加水印",
                        "default": False,
                    },
                    "save_to": {
                        "type": "string",
                        "description": "保存图片到本地目录路径（b64_json 模式必填）",
                    },
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="seedream_web_search_generate",
            description="""联网搜索 + 文生图：结合实时信息生成图片（仅 5.0 模型）。

Seedream 5.0 专属功能，在生图前先搜索互联网获取实时信息，
适合需要结合最新资讯、热点事件或特定知识生成图片的场景。

示例：
- "2024年巴黎奥运会开幕式的精彩瞬间"
- "最新的特斯拉 Cybertruck 在火星表面行驶"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图像描述提示词，可包含对实时信息的要求",
                    },
                    "size": {
                        "type": "string",
                        "description": "输出尺寸",
                        "default": "2K",
                    },
                    "model": {
                        "type": "string",
                        "description": "模型版本（仅 5.0 支持联网搜索）",
                        "default": "doubao-seedream-5-0-260128",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式",
                        "default": "png",
                        "enum": ["png", "jpeg"],
                    },
                    "response_format": {
                        "type": "string",
                        "description": "返回格式: url（返回图片链接）或 b64_json（返回base64编码图片数据）",
                        "default": "url",
                        "enum": ["url", "b64_json"],
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "是否添加水印",
                        "default": False,
                    },
                    "save_to": {
                        "type": "string",
                        "description": "保存图片到本地目录路径（b64_json 模式必填）",
                    },
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="seedream_list_models",
            description="列出可用的 Seedream 模型版本及其特性说明。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict[str, Any],
) -> list[types.TextContent | types.ImageContent]:
    """调用指定的 Seedream 工具"""
    if name == "seedream_text_to_image":
        return await handle_text_to_image(
            prompt=arguments["prompt"],
            size=arguments.get("size", "2K"),
            n=arguments.get("n", 1),
            model=arguments.get("model"),
            output_format=arguments.get("output_format", "png"),
            response_format=arguments.get("response_format", "url"),
            watermark=arguments.get("watermark", False),
            save_to=arguments.get("save_to"),
        )
    elif name == "seedream_image_to_image":
        return await handle_image_to_image(
            prompt=arguments["prompt"],
            image_url=arguments["image_url"],
            size=arguments.get("size", "2K"),
            model=arguments.get("model"),
            scale=arguments.get("scale", 0.5),
            output_format=arguments.get("output_format", "png"),
            response_format=arguments.get("response_format", "url"),
            watermark=arguments.get("watermark", False),
            save_to=arguments.get("save_to"),
        )
    elif name == "seedream_merge_images":
        return await handle_merge_images(
            prompt=arguments["prompt"],
            image_urls=arguments["image_urls"],
            size=arguments.get("size", "2K"),
            model=arguments.get("model"),
            output_format=arguments.get("output_format", "png"),
            response_format=arguments.get("response_format", "url"),
            watermark=arguments.get("watermark", False),
            save_to=arguments.get("save_to"),
        )
    elif name == "seedream_generate_sequence":
        return await handle_generate_sequence(
            prompt=arguments["prompt"],
            max_images=arguments.get("max_images", 4),
            size=arguments.get("size", "2K"),
            model=arguments.get("model"),
            output_format=arguments.get("output_format", "png"),
            response_format=arguments.get("response_format", "url"),
            watermark=arguments.get("watermark", False),
            save_to=arguments.get("save_to"),
        )
    elif name == "seedream_web_search_generate":
        return await handle_web_search_generate(
            prompt=arguments["prompt"],
            size=arguments.get("size", "2K"),
            model=arguments.get("model"),
            output_format=arguments.get("output_format", "png"),
            response_format=arguments.get("response_format", "url"),
            watermark=arguments.get("watermark", False),
            save_to=arguments.get("save_to"),
        )
    elif name == "seedream_list_models":
        return await handle_list_models()
    else:
        raise McpError(types.ErrorData(
            code=-32601,
            message=f"未知工具: {name}",
        ))


@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    """注册提示词模板"""
    return [
        types.Prompt(
            name="seedream_expert",
            description="成为 Seedream 图片生成专家，根据用户需求推荐合适的工具和参数",
        ),
    ]


@server.get_prompt()
async def get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """获取提示词模板"""
    if name == "seedream_expert":
        return types.GetPromptResult(
            description="Seedream 图片生成专家",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=(
                            "你是一位专业的 AI 图片生成专家，擅长使用 Seedream 模型。\n\n"
                            "可用工具：\n"
                            "1. **seedream_text_to_image** - 文生图（通用）\n"
                            "2. **seedream_image_to_image** - 图生图（基于参考图）\n"
                            "3. **seedream_merge_images** - 多图融合\n"
                            "4. **seedream_generate_sequence** - 组图生成\n"
                            "5. **seedream_web_search_generate** - 联网搜索+文生图（5.0 专属）\n"
                            "6. **seedream_list_models** - 查看模型版本\n\n"
                            "请根据用户的需求，推荐最合适的工具和参数配置。"
                        ),
                    ),
                ),
            ],
        )
    raise McpError(types.ErrorData(
        code=-32601,
        message=f"未知提示词: {name}",
    ))


async def main() -> None:
    """启动 MCP Server"""
    # 验证配置
    try:
        settings.validate()
        print(f"✓ Seedream MCP Server 启动中...")
        print(f"  - 模型: {settings.volc_model}")
        print(f"  - API: {settings.volc_base_url}")
        print(f"  - 可用工具: seedream_text_to_image, seedream_image_to_image, "
              f"seedream_merge_images, seedream_generate_sequence, "
              f"seedream_web_search_generate, seedream_list_models")
    except ValueError as e:
        print(f"⚠️  {e}")
        print("  - 你可以在启动后通过环境变量设置，或直接调用工具时传入 api_key")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=settings.server_name,
                server_version=settings.server_version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
