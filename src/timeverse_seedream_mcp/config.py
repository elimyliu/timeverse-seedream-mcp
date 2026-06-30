"""Seedream MCP Server 配置模块."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    """应用配置."""

    # 火山引擎 API 配置
    volc_api_key: str = field(default_factory=lambda: os.getenv("VOLC_API_KEY", ""))
    volc_base_url: str = field(
        default_factory=lambda: os.getenv(
            "VOLC_BASE_URL",
            "https://ark.cn-beijing.volces.com/api/v3",
        )
    )
    volc_model: str = field(
        default_factory=lambda: os.getenv(
            "VOLC_MODEL",
            "doubao-seedream-5-0-260128",
        )
    )

    # MCP 服务器配置
    server_name: str = "timeverse-seedream-mcp"
    server_version: str = "0.1.0"

    def validate(self) -> None:
        """验证配置是否有效."""
        if not self.volc_api_key:
            raise ValueError(
                "VOLC_API_KEY 环境变量未设置。"
                "请设置环境变量 VOLC_API_KEY=your_api_key"
            )

    @property
    def images_generations_url(self) -> str:
        """返回图片生成 API 端点 URL."""
        return f"{self.volc_base_url}/images/generations"

    @property
    def available_models(self) -> dict[str, str]:
        """返回可用的模型列表."""
        return {
            "5.0": "doubao-seedream-5-0-260128",
            "4.5": "doubao-seedream-4-5-251128",
            "4.0": "doubao-seedream-4-0-250828",
        }


# 全局单例
settings = Settings()
