"""
Seedream MCP Server - Pydantic Schemas

数据模型定义，用于请求/响应的类型校验和序列化。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ModelVersion(str, Enum):
    """支持的 Seedream 模型版本"""

    SEEDREAM_5_0 = "doubao-seedream-5-0-260128"
    SEEDREAM_4_5 = "doubao-seedream-4-5-251128"
    SEEDREAM_4_0 = "doubao-seedream-4-0-250828"


class ResponseFormat(str, Enum):
    """响应格式"""

    URL = "url"
    B64_JSON = "b64_json"


class OutputFormat(str, Enum):
    """输出图片格式"""

    PNG = "png"
    JPEG = "jpeg"


class SizePreset(str, Enum):
    """预设尺寸档位"""

    K1 = "1K"
    K2 = "2K"
    K3 = "3K"
    K4 = "4K"


class SequentialMode(str, Enum):
    """组图模式"""

    AUTO = "auto"
    DISABLED = "disabled"


class SeedreamGenerateRequest(BaseModel):
    """文生图请求参数"""

    prompt: str = Field(
        ..., description="图像描述提示词，中英文均可。建议不超过 300 个汉字或 600 个英文单词"
    )
    model: str = Field(
        default=ModelVersion.SEEDREAM_5_0.value,
        description="模型版本",
    )
    size: str = Field(
        default="2K",
        description="输出尺寸。可选: 1K, 2K, 3K, 4K 或自定义如 1920x1080",
    )
    output_format: str = Field(
        default="png",
        description="输出格式: png 或 jpeg (仅 5.0 支持 png)",
    )
    response_format: str = Field(
        default="url",
        description="返回形式: url 或 b64_json",
    )
    watermark: bool = Field(
        default=False,
        description="是否添加水印",
    )
    stream: bool = Field(
        default=False,
        description="是否流式输出",
    )


class SeedreamGenerateMultiRequest(BaseModel):
    """文生组图请求参数"""

    prompt: str = Field(
        ..., description="图像描述提示词"
    )
    model: str = Field(
        default=ModelVersion.SEEDREAM_5_0.value,
        description="模型版本（需 4.5 或 5.0）",
    )
    size: str = Field(
        default="2K",
        description="输出尺寸",
    )
    max_images: int = Field(
        default=4,
        description="生成图片数量 (1-15)",
        ge=1,
        le=15,
    )
    output_format: str = Field(
        default="png",
        description="输出格式",
    )
    watermark: bool = Field(
        default=False,
        description="是否添加水印",
    )


class SeedreamImageToImageRequest(BaseModel):
    """图生图请求参数"""

    prompt: str = Field(
        ..., description="图像描述提示词，描述对参考图的修改"
    )
    image_url: str = Field(
        ..., description="参考图片 URL"
    )
    model: str = Field(
        default=ModelVersion.SEEDREAM_5_0.value,
        description="模型版本（需 4.5 或 5.0）",
    )
    size: str = Field(
        default="2K",
        description="输出尺寸",
    )
    scale: float = Field(
        default=0.5,
        description="文本描述影响程度 (0-1)，越大文本影响越大",
        ge=0.0,
        le=1.0,
    )
    output_format: str = Field(
        default="png",
        description="输出格式",
    )
    watermark: bool = Field(
        default=False,
        description="是否添加水印",
    )


class SeedreamMergeImagesRequest(BaseModel):
    """多图融合请求参数"""

    prompt: str = Field(
        ..., description="融合描述，可用「图1」「图2」指代各图片"
    )
    image_urls: list[str] = Field(
        ..., description="参考图片 URL 列表 (最多 10 张)", max_length=10
    )
    model: str = Field(
        default=ModelVersion.SEEDREAM_5_0.value,
        description="模型版本（需 4.5 或 5.0）",
    )
    size: str = Field(
        default="2K",
        description="输出尺寸",
    )
    output_format: str = Field(
        default="png",
        description="输出格式",
    )
    watermark: bool = Field(
        default=False,
        description="是否添加水印",
    )


class SeedreamWebSearchRequest(BaseModel):
    """联网搜索 + 文生图请求参数 (仅 5.0)"""

    prompt: str = Field(
        ..., description="图像描述提示词，可包含对实时信息的要求"
    )
    model: str = Field(
        default=ModelVersion.SEEDREAM_5_0.value,
        description="模型版本（需 5.0）",
    )
    size: str = Field(
        default="2K",
        description="输出尺寸",
    )
    output_format: str = Field(
        default="png",
        description="输出格式",
    )
    watermark: bool = Field(
        default=False,
        description="是否添加水印",
    )


class ImageData(BaseModel):
    """API 返回的单张图片数据"""

    url: Optional[str] = Field(default=None, description="图片 URL")
    b64_json: Optional[str] = Field(default=None, description="Base64 编码的图片数据")
    revised_prompt: Optional[str] = Field(default=None, description="优化后的提示词")


class SeedreamResponse(BaseModel):
    """API 响应"""

    created: int = Field(..., description="创建时间戳")
    data: list[ImageData] = Field(..., description="图片数据列表")
