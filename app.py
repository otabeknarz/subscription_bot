import asyncio
import logging

from modules.models import get_main_bot


async def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    await get_main_bot().start_main_bot()


if __name__ == "__main__":
    asyncio.run(main())
