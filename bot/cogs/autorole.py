from discord.ext import commands

# Basic in-memory autorole mapping. Persist to DB for production.
autoroles = {}  # guild_id -> role_id

class AutoRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_autorole(self, guild_id: int):
        if guild_id in autoroles:
            return
        try:
            from bot.services.db import get_sessionmaker, get_guild_config
            Session = get_sessionmaker()
            async with Session() as session:
                cfg = await get_guild_config(session, guild_id)
                if cfg.autorole_id:
                    autoroles[guild_id] = cfg.autorole_id
        except Exception:
            return

    @commands.command(name="setautorole")
    @commands.has_permissions(manage_roles=True)
    async def set_autorole(self, ctx: commands.Context, role_id: int):
        autoroles[ctx.guild.id] = role_id
        # persist
        try:
            from bot.services.db import get_sessionmaker, upsert_guild_config
            Session = get_sessionmaker()
            async with Session() as session:
                await upsert_guild_config(session, ctx.guild.id, autorole_id=role_id)
        except Exception:
            pass
        await ctx.send(f"Set autorole to <@&{role_id}>")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self._ensure_autorole(member.guild.id)
        role_id = autoroles.get(member.guild.id)
        if not role_id:
            return
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role, reason="AutoRole")
            except Exception:
                pass


def setup(bot: commands.Bot):
    bot.add_cog(AutoRole(bot))
