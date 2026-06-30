"""Seedream MCP Server - 入口模块"""

import sys
import asyncio
from .server import main


def cli() -> None:
    """同步入口，供 entry_points 脚本调用"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    cli()
