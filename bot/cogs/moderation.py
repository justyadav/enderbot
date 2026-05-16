import discord
from discord import app_commands
from discord.ext import commands
import datetime
import json
from typing import Optional

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channels = {}
        self.load_logs()

    # --- PERSISTENCE LOGIC ---
    def save_logs(self):
        with open("logs.json", "w") as f:
            json.dump(self.log_channels, f)

    def load_logs(self):
        try:
            with open("logs.json", "r") as f:
                self.log_channels = json.load(f)
        except FileNotFoundError:
            self.log_channels = {}

    # --- LOGGING SETUP ---
    @app_commands.command(name="set_logging", description="Sets the channel for moderation logs")
    @app_commands.describe(channel="The channel where logs will be sent")
    async def set_logging(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("❌ Only the bot owner can use this.", ephemeral=True)
        
        self.log_channels[str(interaction.guild.id)] = channel.id
        self.save_logs()
        await interaction.response.send_message(f"✅ Logging channel set to {channel.mention}")

    # --- BASIC MODERATION ---
    @app_commands.command(name="kick", description="Kicks a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ Kicked {member.name}")

    @app_commands.command(name="ban", description="Bans a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 Banned {member.name}")

    @app_commands.command(name="timeout", description="Mutes a member temporarily")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await interaction.response.send_message(f"🤫 Timed out {member.name} for {minutes}m.")

    @app_commands.command(name="clear", description="Purge messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.")

    # --- ROLE MANAGEMENT GROUP ---
    role_group = app_commands.Group(name="role", description="Role commands")

    @role_group.command(name="add", description="Add a role to a member")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_add(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Added {role.name} to {member.name}")

    @role_group.command(name="remove", description="Remove a role from a member")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_remove(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await interaction.response.send_message(f"❌ Removed {role.name} from {member.name}")

    # --- LOGGING LISTENERS ---
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot: return
        gid = str(message.guild.id)
        if gid in self.log_channels:
            channel = self.bot.get_channel(self.log_channels[gid])
            if channel:
                embed = discord.Embed(title="🗑️ Message Deleted", color=discord.Color.red())
                embed.add_field(name="User", value=message.author.mention)
                embed.add_field(name="Channel", value=message.channel.mention)
                embed.add_field(name="Content", value=message.content or "No text content", inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        gid = str(member.guild.id)
        if gid in self.log_channels:
            channel = self.bot.get_channel(self.log_channels[gid])
            if channel:
                embed = discord.Embed(title="🚪 Member Left/Kicked", description=f"{member.name} left the server.", color=discord.Color.orange())
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))