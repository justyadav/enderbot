import discord
from discord import app_commands
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        latency = self.bot.latency * 1000  # Convert to milliseconds
        await interaction.response.send_message(f'Pong! Latency: {latency:.2f} ms')

# This is the missing piece:
async def setup(bot):
    await bot.add_cog(General(bot))