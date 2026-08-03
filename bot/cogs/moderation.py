from discord.ext import commands
from discord import Member
import re

class Moderation(commands.Cog):
    """Simple moderation cog with a sample ping command and a basic anti-caps filter.
    Extend this cog with database-driven thresholds and more checks.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Simple ping command to check bot responsiveness."""
        await ctx.send("Pong!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Basic anti-caps: if message > 8 chars and more than 70% caps, delete and warn
        content = message.content or ""
        if len(content) > 8:
            letters = re.findall(r"[A-Za-z]", content)
            if letters:
                caps = sum(1 for c in letters if c.isupper())
                ratio = caps / len(letters)
                if ratio > 0.7:
                    try:
                        await message.delete()
                        await message.channel.send(f"{message.author.mention} Please avoid excessive caps.")
                    except Exception:
                        pass


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot))
