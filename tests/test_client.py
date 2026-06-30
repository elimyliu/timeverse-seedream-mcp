"""
Seedream MCP Server - 客户端单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from timeverse_seedream_mcp.client import SeedreamClient, SeedreamResponse, SeedreamImageResult


@pytest.fixture
def mock_client():
    """创建模拟客户端"""
    with patch("timeverse_seedream_mcp.client.httpx.AsyncClient") as mock_http:
        client = SeedreamClient(api_key="test_key")
        yield client


class TestSeedreamClient:
    """测试 Seedream 客户端"""

    def test_init_without_api_key(self):
        """测试未设置 API Key 时抛出异常"""
        with patch("timeverse_seedream_mcp.client.settings") as mock_settings:
            mock_settings.volc_api_key = ""
            mock_settings.volc_base_url = "https://ark.cn-beijing.volces.com/api/v3"
            mock_settings.volc_model = "doubao-seedream-5-0-260128"
            with pytest.raises(ValueError, match="VOLC_API_KEY"):
                SeedreamClient(api_key="")

    def test_init_with_api_key(self):
        """测试正常初始化"""
        client = SeedreamClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.base_url == "https://ark.cn-beijing.volces.com/api/v3"

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_client):
        """测试文生图成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "created": 1234567890,
            "data": [
                {
                    "url": "https://example.com/image.png",
                    "revised_prompt": "优化后的提示词",
                }
            ],
        }
        mock_client._client.post = AsyncMock(return_value=mock_response)

        result = await mock_client.generate(prompt="一只猫", size="2K")

        assert isinstance(result, SeedreamResponse)
        assert len(result.data) == 1
        assert result.data[0].url == "https://example.com/image.png"
        assert result.data[0].revised_prompt == "优化后的提示词"

    @pytest.mark.asyncio
    async def test_generate_with_b64(self, mock_client):
        """测试返回 base64 格式"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "created": 1234567890,
            "data": [
                {
                    "b64_json": "dGVzdF9pbWFnZV9kYXRh",
                    "revised_prompt": "优化后的提示词",
                }
            ],
        }
        mock_client._client.post = AsyncMock(return_value=mock_response)

        result = await mock_client.generate(
            prompt="一只猫", size="2K", response_format="b64_json"
        )

        assert result.data[0].b64_json == "dGVzdF9pbWFnZV9kYXRh"

    @pytest.mark.asyncio
    async def test_generate_with_image_urls(self, mock_client):
        """测试图生图模式"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "created": 1234567890,
            "data": [{"url": "https://example.com/new_image.png"}],
        }
        mock_client._client.post = AsyncMock(return_value=mock_response)

        result = await mock_client.generate(
            prompt="改成油画风格",
            size="2K",
            n=1,
            image_urls=["https://example.com/reference.jpg"],
        )

        assert result.data[0].url == "https://example.com/new_image.png"

    @pytest.mark.asyncio
    async def test_generate_sequence(self, mock_client):
        """测试组图生成模式"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "created": 1234567890,
            "data": [
                {"url": "https://example.com/img_1.png", "index": 1},
                {"url": "https://example.com/img_2.png", "index": 2},
                {"url": "https://example.com/img_3.png", "index": 3},
                {"url": "https://example.com/img_4.png", "index": 4},
            ],
        }
        mock_client._client.post = AsyncMock(return_value=mock_response)

        result = await mock_client.generate(
            prompt="四季变迁",
            size="2K",
            n=1,
            sequential="auto",
            max_images=4,
        )

        assert len(result.data) == 4
        assert result.data[0].index == 1

    @pytest.mark.asyncio
    async def test_generate_with_tools(self, mock_client):
        """测试联网搜索模式"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "created": 1234567890,
            "data": [{"url": "https://example.com/image.png"}],
        }
        mock_client._client.post = AsyncMock(return_value=mock_response)

        web_search_tool = {
            "type": "web_search",
            "web_search": {
                "search_mode": "auto",
                "search_scope": "interNet",
                "enable_enhancement": True,
            },
        }

        result = await mock_client.generate(
            prompt="2024年巴黎奥运会开幕式",
            size="2K",
            tools=[web_search_tool],
        )

        assert len(result.data) == 1

    @pytest.mark.asyncio
    async def test_generate_stream(self, mock_client):
        """测试流式输出"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        async def mock_lines():
            yield b"data: {\"created\": 123, \"data\": [{\"url\": \"https://example.com/img.png\"}]}\n\n"
            yield b"data: [DONE]\n\n"

        mock_response.aiter_lines = lambda: mock_lines()
        mock_client._client.stream = MagicMock(return_value=mock_response)

        results = []
        async for chunk in mock_client.generate_stream(prompt="测试", size="2K"):
            results.append(chunk)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_close(self, mock_client):
        """测试关闭客户端"""
        mock_client._client.aclose = AsyncMock()
        await mock_client.close()
        mock_client._client.aclose.assert_called_once()
