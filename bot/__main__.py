"""Entry point for the bot package. Run with: python -m bot
"""
import asyncio
from bot.bot import run_bot

if __name__ == "__main__":
    asyncio.run(run_bot())
