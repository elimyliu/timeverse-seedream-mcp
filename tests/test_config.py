"""配置模块测试"""

import os
from timeverse_seedream_mcp.config import Settings, settings


def test_settings_defaults():
    """测试默认配置"""
    assert settings.server_name == "timeverse-seedream-mcp"
    assert settings.server_version == "0.1.0"
    assert "ark.cn-beijing.volces.com" in settings.volc_base_url


def test_images_generations_url():
    """测试 API 端点 URL 生成"""
    expected = (
        f"{settings.volc_base_url}/images/generations"
    )
    assert settings.images_generations_url == expected


def test_available_models():
    """测试可用模型列表"""
    models = settings.available_models
    assert "5.0" in models
    assert "4.5" in models
    assert "4.0" in models
    assert models["5.0"] == "doubao-seedream-5-0-260128"
    assert models["4.5"] == "doubao-seedream-4-5-251128"
    assert models["4.0"] == "doubao-seedream-4-0-250828"


def test_settings_validation():
    """测试配置验证"""
    s = Settings(volc_api_key="")
    try:
        s.validate()
        assert False, "应该抛出异常"
    except ValueError:
        pass
