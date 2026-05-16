#!/usr/bin/env python3
"""
AI Smart Search - Stdio entry point for MCP bundle.
"""

import asyncio
import sys

# Ensure the bundle directory is on the path
sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")

from server import main

if __name__ == "__main__":
    asyncio.run(main())
