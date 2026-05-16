import discord
from discord import app_commands
from discord.ext import commands

class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # In a production bot, you'd save this ID to a database or JSON file
        self.log_channel_id = None 

    @app_commands.command(name="log_setup", description="Set the channel where server logs will be sent")
    @app_commands.checks.has_permissions(administrator=True)
    async def log_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.log_channel_id = channel.id
        
        embed = discord.Embed(
            title="📜 Logging System Active",
            description=f"All server events will now be logged in {channel.mention}.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # --- EVENT: MESSAGE EDIT ---
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not self.log_channel_id:
            return
        
        if before.content == after.content:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            embed = discord.Embed(title="📝 Message Edited", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
            embed.set_author(name=before.author, icon_url=before.author.display_avatar.url)
            embed.add_field(name="Before", value=before.content or "No content", inline=False)
            embed.add_field(name="After", value=after.content or "No content", inline=False)
            embed.add_field(name="Channel", value=before.channel.mention, inline=True)
            await log_channel.send(embed=embed)

    # --- EVENT: MESSAGE DELETE ---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not self.log_channel_id:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            embed = discord.Embed(title="🗑️ Message Deleted", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
            embed.add_field(name="Content", value=message.content or "No content (Image/Embed)", inline=False)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            await log_channel.send(embed=embed)

    # --- EVENT: MEMBER JOIN ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not self.log_channel_id:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            embed = discord.Embed(title="📥 Member Joined", color=discord.Color.green(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="User", value=f"{member.mention} ({member.name})", inline=False)
            embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, style='R'), inline=True)
            embed.set_footer(text=f"ID: {member.id}")
            await log_channel.send(embed=embed)

    # --- EVENT: MEMBER REMOVE ---
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not self.log_channel_id:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            embed = discord.Embed(title="📤 Member Left", color=discord.Color.light_grey(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="User", value=f"{member.name}", inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerLogs(bot))