# Seedream MCP Server

基于火山引擎 Seedream 模型的图片生成 MCP 服务器。

通过 MCP (Model Context Protocol) 协议，让 AI 助手能够调用 Seedream 模型生成高质量图片。

## 功能特性

- ✨ **文生图 (Text-to-Image)**：根据文本描述生成图片
- ✨ **文生组图 (Text-to-Multi-Image)**：根据文本描述生成多张图片（4.5/5.0 版本）
- 🖼️ **图生图 (Image-to-Image)**：基于参考图片生成新图片（4.5/5.0 版本）
- 🖼️ **多图融合 (Multi-Image Fusion)**：融合多张图片生成新图片（4.5/5.0 版本）
- 🔗 **联网搜索 (Web Search - 5.0)**：结合联网搜索结果生成图片
- ⚡ **流式输出 (Streaming)**：支持流式返回生成的图片
- 🔄 **所有输出为 Markdown 格式**，方便 AI 直接展示

## 快速开始

### 前提条件

- Python 3.10+
- 火山引擎 API Key（[获取方式](https://www.volcengine.com/docs/82379/1099320)）

### 安装

```bash
pip install timeverse-seedream-mcp
```

### 配置环境变量

```bash
export VOLC_API_KEY="your-api-key-here"
# 可选，默认为 doubao-seedream-5-0-260128
export VOLC_MODEL="doubao-seedream-5-0-260128"
```

### 运行

```bash
timeverse-seedream-mcp
```

### MCP 配置

将以下配置添加到你的 MCP 客户端配置文件中：

```json
{
  "mcpServers": {
    "seedream": {
      "command": "timeverse-seedream-mcp",
      "env": {
        "VOLC_API_KEY": "your-api-key-here",
        "VOLC_MODEL": "doubao-seedream-5-0-260128"
      }
    }
  }
}
```

## 工具列表

| 工具名称 | 描述 | 适用模型 |
|---------|------|---------|
| `seedream_generate` | 文生图 - 根据文本描述生成图片 | 所有版本 |
| `seedream_generate_multi` | 文生组图 - 根据文本生成多张不同图片 | 4.5/5.0 |
| `seedream_image_to_image` | 图生图 - 基于参考图片生成新图片 | 4.5/5.0 |
| `seedream_merge_images` | 多图融合 - 融合多张图片生成新图片 | 4.5/5.0 |

## API 参考

### Base URL

```
https://ark.cn-beijing.volces.com/api/v3
```

### 兼容性

本 API 完全兼容 OpenAI Images API 格式，可以使用 OpenAI SDK 直接调用。

### 模型版本

| 模型 | 版本 | 支持功能 |
|------|------|---------|
| `doubao-seedream-5-0-260128` | 5.0 | 文生图、文生组图、图生图、多图融合、联网搜索、流式 |
| `doubao-seedream-4-5-251128` | 4.5 | 文生图、文生组图、图生图、多图融合、流式 |
| `doubao-seedream-4-0-250828` | 4.0 | 文生图、流式 |

## 开发

```bash
# 克隆仓库
git clone https://github.com/your-org/timeverse-seedream-mcp.git
cd timeverse-seedream-mcp

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行 Lint
ruff check src/
mypy src/
```
