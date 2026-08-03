"""Bot factory and runner. Keeps the main entry small and loads cogs from bot/cogs.
"""
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Load .env from repo root if present
load_dotenv(dotenv_path=Path.cwd() / ".env")

logger = logging.getLogger("ender_bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True
INTENTS.members = True  # enable only if needed

DEFAULT_PREFIX = os.getenv("PREFIX", "!")
BOT_NAME = os.getenv("BOT_NAME", "Ender Bot")
DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "YADUVANSHI1816_")
CUSTOM_STATUS = os.getenv("CUSTOM_STATUS", f"Developed by {DEVELOPER_NAME} | /help")

async def run_bot():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment")
        return

    # Initialize DB (if configured). Uses DATABASE_URL env var or defaults to sqlite+aiosqlite://./data.db
    try:
        from bot.services.db import init_db
        await init_db(os.getenv("DATABASE_URL"))
    except Exception:
        logger.exception("DB initialization failed (continuing without DB)")

    bot = commands.Bot(
        command_prefix=DEFAULT_PREFIX,
        intents=INTENTS,
        application_id=os.getenv("APPLICATION_ID"),
        activity=discord.CustomActivity(name=CUSTOM_STATUS),
        status=discord.Status.online,
    )

    # Load all cogs in bot/cogs
    cogs_path = Path(__file__).parent / "cogs"
    for path in cogs_path.glob("*.py"):
        if path.name == "__init__.py":
            continue
        cog_name = f"bot.cogs.{path.stem}"
        try:
            bot.load_extension(cog_name)
            logger.info(f"Loaded cog: {cog_name}")
        except Exception as e:
            logger.exception(f"Failed to load cog {cog_name}: {e}")

    @bot.event
    async def on_ready():
        logger.info(f"Bot ready: {BOT_NAME} ({bot.user}) (ID: {bot.user.id})")
        try:
            if bot.user and bot.user.name != BOT_NAME:
                await bot.user.edit(username=BOT_NAME)
                logger.info(f"Renamed bot to {BOT_NAME}")
        except Exception as exc:
            logger.warning(f"Could not rename bot user: {exc}")

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.close()
