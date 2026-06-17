import discord
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.has_permissions(administrator=True)
    @commands.hybrid_command(name="setprefix", description="Change the bot prefix for this server.")
    async def set_prefix(self, ctx: commands.Context, new_prefix: str):
        """Updates prefix via Discord chat and immediately saves to Mongo"""
        guild_id = ctx.guild.id

        # Update the shared MongoDB database
        await self.db.settings.update_one(
            {"guild_id": guild_id},
            {"$set": {"prefix": new_prefix}},
            upsert=True
        )

        await ctx.send(f"✅ Prefix has been successfully updated to `{new_prefix}` (Changes will reflect on your Web Dashboard).")

    @commands.hybrid_command(name="currentprefix", description="View the active server prefix.")
    async def current_prefix(self, ctx: commands.Context):
        """Fetches live configuration from MongoDB"""
        guild_id = ctx.guild.id
        guild_config = await self.db.settings.find_one({"guild_id": guild_id})
        
        prefix = guild_config.get("prefix", "!") if guild_config else "!"
        await ctx.send(f"The active prefix for this server is `{prefix}`")

async def setup(bot):
    await bot.add_cog(Settings(bot))