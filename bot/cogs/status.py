import discord
from discord import app_commands
from discord.ext import commands
import time
import datetime
import platform
import psutil

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="status", description="Shows the bot's current health and performance")
    async def status(self, interaction: discord.Interaction):
        # Calculate Uptime
        current_time = time.time()
        difference = int(round(current_time - self.start_time))
        uptime = str(datetime.timedelta(seconds=difference))

        # System Info
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        
        # Command Count
        total_commands = len(self.bot.tree.get_commands())

        embed = discord.Embed(title="🤖 System Status", color=discord.Color.green())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name="Uptime", value=f"`{uptime}`", inline=True)
        embed.add_field(name="Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="Command Count", value=f"`{total_commands} Loaded`", inline=True)
        
        embed.add_field(name="CPU Usage", value=f"`{cpu_usage}%`", inline=True)
        embed.add_field(name="RAM Usage", value=f"`{ram_usage}%`", inline=True)
        embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        
        embed.set_footer(text=f"Running on Python {platform.python_version()}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uptime", description="Check how long the bot has been running")
    async def uptime(self, interaction: discord.Interaction):
        current_time = time.time()
        difference = int(round(current_time - self.start_time))
        uptime_str = str(datetime.timedelta(seconds=difference))
        await interaction.response.send_message(f"🚀 I have been online for: `{uptime_str}`")

    @app_commands.command(name="invite", description="Get the link to invite this bot to your server")
    async def invite(self, interaction: discord.Interaction):
        # Update with your actual client ID or use a dynamic link
        invite_link = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        
        embed = discord.Embed(
            title="Invite Me!",
            description=f"Click [HERE]({invite_link}) to invite the bot to your server.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Status(bot))