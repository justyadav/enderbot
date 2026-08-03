from typing import Dict
from discord.ext import commands
from discord import RawReactionActionEvent

# In-memory mapping: guild_id -> message_id -> {emoji: role_id}
# Persist this in DB for production use
reaction_panels: Dict[int, Dict[int, Dict[str, int]]] = {}

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="rr-create")
    @commands.has_permissions(manage_roles=True)
    async def rr_create(self, ctx: commands.Context, message_id: int, emoji: str, role_id: int):
        """Add a mapping: reacts on message_id with emoji -> gives role_id"""
        guild_map = reaction_panels.setdefault(ctx.guild.id, {})
        msg_map = guild_map.setdefault(message_id, {})
        msg_map[emoji] = role_id
        await ctx.send(f"Reaction role set: message={message_id} emoji={emoji} role={role_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Only handle in guilds
        if payload.guild_id is None:
            return
        guild_map = reaction_panels.get(payload.guild_id)
        if not guild_map:
            return
        msg_map = guild_map.get(payload.message_id)
        if not msg_map:
            return
        key = str(payload.emoji)
        role_id = msg_map.get(key) or msg_map.get(getattr(payload.emoji, 'name', ''))
        if role_id:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if member:
                role = guild.get_role(role_id)
                if role:
                    try:
                        await member.add_roles(role, reason="Reaction role")
                    except Exception:
                        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        # Remove role when reaction removed
        if payload.guild_id is None:
            return
        guild_map = reaction_panels.get(payload.guild_id)
        if not guild_map:
            return
        msg_map = guild_map.get(payload.message_id)
        if not msg_map:
            return
        key = str(payload.emoji)
        role_id = msg_map.get(key) or msg_map.get(getattr(payload.emoji, 'name', ''))
        if role_id:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if member:
                role = guild.get_role(role_id)
                if role:
                    try:
                        await member.remove_roles(role, reason="Reaction role removed")
                    except Exception:
                        pass


def setup(bot: commands.Bot):
    bot.add_cog(ReactionRoles(bot))
