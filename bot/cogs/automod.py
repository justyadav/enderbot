import re
import time
from collections import defaultdict, deque
from discord.ext import commands

# NOTE: This is an in-memory basic Automod proof-of-concept.
# For production you must back guild settings and rate-limits to Redis/Postgres

INVITE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:discord(?:app)?\.com/invite|discord.gg)/[A-Za-z0-9-]+", re.I)
URL_REGEX = re.compile(r"https?://\S+", re.I)

class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # per-guild: user -> deque of timestamps (for spam detection)
        self._message_times = defaultdict(lambda: defaultdict(lambda: deque(maxlen=8)))
        # per-guild toggles (in-memory cache); persistent storage will be used when available
        self.guild_settings = defaultdict(lambda: {
            "automod_enabled": True,
            "anti_invite": True,
            "anti_link": False,
            "anti_mention_spam": True,
            "anti_emoji_spam": True,
            "caps_threshold": 0.75,
        })

    async def _load_guild_cfg(self, guild_id: int):
        """Try to load the guild config from DB and cache it in memory.
        Fail silently if DB is not available."""
        if guild_id in self.guild_settings:
            return
        try:
            from bot.services.db import get_sessionmaker, get_guild_config
            Session = get_sessionmaker()
            async with Session() as session:
                cfg = await get_guild_config(session, guild_id)
                self.guild_settings[guild_id] = {
                    "automod_enabled": cfg.automod_enabled,
                    "anti_invite": cfg.anti_invite,
                    "anti_link": cfg.anti_link,
                    "anti_mention_spam": cfg.anti_mention_spam,
                    "anti_emoji_spam": cfg.anti_emoji_spam,
                    "caps_threshold": cfg.caps_threshold,
                }
        except Exception:
            # DB not initialized or failed — keep in-memory defaults
            return

    @commands.group(name="automod", invoke_without_command=True)
    async def automod_group(self, ctx: commands.Context):
        """View automod status"""
        await self._load_guild_cfg(ctx.guild.id)
        cfg = self.guild_settings[ctx.guild.id]
        lines = [f"{k}: {v}" for k, v in cfg.items()]
        await ctx.send("Automod settings:\n" + "\n".join(lines))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        # load DB-backed config once per guild on first use
        if message.guild.id not in self.guild_settings:
            await self._load_guild_cfg(message.guild.id)
        cfg = self.guild_settings[message.guild.id]
        if not cfg.get("automod_enabled", True):
            return

        # Invite check
        if cfg.get("anti_invite") and INVITE_REGEX.search(message.content):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Posting invites is not allowed.")
            except Exception:
                pass
            return

        # Link check
        if cfg.get("anti_link") and URL_REGEX.search(message.content):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Posting links is not allowed.")
            except Exception:
                pass
            return

        # Mention spam: if mentions > 5
        if cfg.get("anti_mention_spam") and len(message.mentions) >= 5:
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Mention spam is not allowed.")
            except Exception:
                pass
            return

        # Emoji spam: crude check counting occurrences of :name: or unicode emojis
        if cfg.get("anti_emoji_spam"):
            emoji_like = re.findall(r":\w+:", message.content)
            if len(emoji_like) >= 10:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Emoji spam detected.")
                except Exception:
                    pass
                return

        # Simple spam rate-limit: 5 messages in 7 seconds -> delete
        now = time.time()
        user_deque = self._message_times[message.guild.id][message.author.id]
        user_deque.append(now)
        if len(user_deque) >= 5 and (now - user_deque[0]) < 7:
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Please stop spamming.")
            except Exception:
                pass


def setup(bot: commands.Bot):
    bot.add_cog(AutoMod(bot))
