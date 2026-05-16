import discord
from discord import app_commands
from discord.ext import commands
import time
import datetime
import platform

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        lat = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: `{lat}ms`")

    @app_commands.command(name="uptime", description="Check how long the bot has been online")
    async def uptime(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        await interaction.response.send_message(f"🚀 **Uptime:** `{uptime_str}`")

    @app_commands.command(name="botinfo", description="Detailed technical information about the bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Ender Bot Information", color=discord.Color.blue())
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds)}", inline=True)
        embed.add_field(name="Commands Loaded", value=f"{len(self.bot.tree.get_commands())}", inline=True)
        embed.set_footer(text="Developed by [Yaduvanshi1816_]")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="membercount", description="Show the total number of members in this server")
    async def membercount(self, interaction: discord.Interaction):
        total = interaction.guild.member_count
        # Optional: break down by humans vs bots
        bots = sum(m.bot for m in interaction.guild.members)
        humans = total - bots
        
        embed = discord.Embed(title=f"📊 {interaction.guild.name} Members", color=discord.Color.green())
        embed.add_field(name="Total", value=f"`{total}`", inline=False)
        embed.add_field(name="Humans", value=f"`{humans}`", inline=True)
        embed.add_field(name="Bots", value=f"`{bots}`", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="changelog", description="See the latest updates to Ender Bot")
    async def changelog(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📝 Latest Updates", color=discord.Color.purple())
        embed.add_field(name="Version 1.5.0", value=(
            "• Added Advanced Logging System\n"
            "• Added Invite Tracking & Leaderboards\n"
            "• Finished the 100+ Command Milestone!\n"
            "• Improved Ticket transcript formatting."
        ), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))