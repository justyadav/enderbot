from discord.ext import commands
from discord import TextChannel

# Basic in-memory guild logging channel mapping. Persist to DB for production.
logging_channels = {}  # guild_id -> {"member": channel_id, "message": channel_id}

class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_logging_cfg(self, guild_id: int):
        if guild_id in logging_channels:
            return
        try:
            from bot.services.db import get_sessionmaker, get_guild_config
            Session = get_sessionmaker()
            async with Session() as session:
                cfg = await get_guild_config(session, guild_id)
                if cfg.logging_channels:
                    logging_channels[guild_id] = cfg.logging_channels
        except Exception:
            return

    @commands.command(name="setlog")
    @commands.has_permissions(manage_guild=True)
    async def setlog(self, ctx: commands.Context, which: str, channel: TextChannel):
        """Set a logging channel: which in [member,message,mod,voice]"""
        guild_map = logging_channels.setdefault(ctx.guild.id, {})
        guild_map[which] = channel.id
        # persist to DB
        try:
            from bot.services.db import get_sessionmaker, upsert_guild_config
            Session = get_sessionmaker()
            async with Session() as session:
                # read existing channels, merge
                cfg = await get_guild_config(session, ctx.guild.id)
                chs = cfg.logging_channels or {}
                chs[which] = channel.id
                await upsert_guild_config(session, ctx.guild.id, logging_channels=chs)
        except Exception:
            pass
        await ctx.send(f"Set {which} logs to {channel.mention}")

    async def _send_to_channel(self, guild_id: int, which: str, content: str):
        await self._ensure_logging_cfg(guild_id)
        gid_map = logging_channels.get(guild_id)
        if not gid_map:
            return
        chan_id = gid_map.get(which)
        if not chan_id:
            return
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(chan_id)
        if not isinstance(channel, TextChannel):
            return
        try:
            await channel.send(content)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self._send_to_channel(member.guild.id, "member", f"Member joined: {member} ({member.id})")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self._send_to_channel(member.guild.id, "member", f"Member left: {member} ({member.id})")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        await self._send_to_channel(message.guild.id, "message", f"Message deleted in #{message.channel}: {message.content}")


def setup(bot: commands.Bot):
    bot.add_cog(LoggingCog(bot))
