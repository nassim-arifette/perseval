import asyncio
import sys

import uvicorn


if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        # Fallback for non-Windows or older Python versions where this policy is unavailable.
        pass


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=5371,
        reload=False,
    )

