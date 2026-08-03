import asyncio
import random
from datetime import timedelta
from discord.ext import commands

# Very basic giveaway implementation using in-process sleep.
# Production: schedule via a durable job queue (Redis + worker) so restarts don't lose giveaways.

active_giveaways = {}  # guild_id -> message_id -> giveaway_info

class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="gstart")
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx: commands.Context, duration_seconds: int, *, prize: str):
        """Start a giveaway. Usage: !gstart 3600 Nitro"""
        msg = await ctx.send(f"🎉 Giveaway started for **{prize}**! React with 🎉 to enter. Ends in {duration_seconds}s")
        await msg.add_reaction("🎉")
        guild_map = active_giveaways.setdefault(ctx.guild.id, {})
        guild_map[msg.id] = {"prize": prize, "message_id": msg.id}

        # schedule finish
        async def _finish():
            await asyncio.sleep(duration_seconds)
            channel = msg.channel
            message = await channel.fetch_message(msg.id)
            users = set()
            for reaction in message.reactions:
                if str(reaction.emoji) == "🎉":
                    async for user in reaction.users():
                        if not user.bot:
                            users.add(user)
            if not users:
                await channel.send("No valid participants for the giveaway.")
                return
            winner = random.choice(list(users))
            await channel.send(f"🎉 Giveaway ended! Winner: {winner.mention} — Prize: {prize}")
            # cleanup
            guild_map.pop(msg.id, None)

        asyncio.create_task(_finish())

    @commands.command(name="greroll")
    @commands.has_permissions(manage_guild=True)
    async def greroll(self, ctx: commands.Context, message_id: int):
        """Reroll a giveaway by message_id (best-effort)."""
        try:
            msg = await ctx.channel.fetch_message(message_id)
        except Exception:
            await ctx.send("Message not found in this channel")
            return
        users = set()
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.add(user)
        if not users:
            await ctx.send("No participants to reroll.")
            return
        winner = random.choice(list(users))
        await ctx.send(f"🎉 New winner: {winner.mention}")


def setup(bot: commands.Bot):
    bot.add_cog(Giveaways(bot))
