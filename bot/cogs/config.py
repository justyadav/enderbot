import discord
from discord import app_commands
from discord.ext import commands

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- PREFIX CONFIGURATION ---
    @app_commands.command(name="set_prefix", description="Change the bot's text prefix")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: discord.Interaction, new_prefix: str):
        # In a full bot, you would save this to a database
        await interaction.response.send_message(f"✅ Prefix updated to: `{new_prefix}`")

    # --- NICKNAME MANAGEMENT ---
    @app_commands.command(name="set_botname", description="Change the bot's nickname in this server")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def set_botname(self, interaction: discord.Interaction, name: str):
        await interaction.guild.me.edit(nick=name)
        await interaction.response.send_message(f"✅ My nickname is now **{name}**")

    # --- CHANNEL MANAGEMENT ---
    config_group = app_commands.Group(name="config", description="Deep server configuration")

    @config_group.command(name="announce_channel", description="Set the channel for bot announcements") 
    async def set_announce(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.send_message(f"📢 Announcements will now be sent to {channel.mention}")

    @config_group.command(name="rules_channel", description="Link the server rules channel to the bot")
    async def set_rules(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.send_message(f"📜 Rules channel set to {channel.mention}")

    # --- EMERGENCY TOOLS ---
    @app_commands.command(name="emergency_lockdown", description="Locks EVERY text channel in the server")
    @app_commands.checks.has_permissions(administrator=True)
    async def mass_lock(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        for channel in interaction.guild.text_channels:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.followup.send("🚨 **SERVER-WIDE LOCKDOWN INITIATED.**")

    @app_commands.command(name="emergency_unlock", description="Unlocks EVERY text channel in the server")
    @app_commands.checks.has_permissions(administrator=True)
    async def mass_unlock(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        for channel in interaction.guild.text_channels:
            await channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.followup.send("🔓 Server-wide lockdown lifted.")

async def setup(bot):
    await bot.add_cog(Config(bot))