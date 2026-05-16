import discord
from discord import app_commands
from discord.ext import commands

class ServerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="slowmode", description="Set the slowmode for the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"⌛ Slowmode set to {seconds} seconds.")

    @app_commands.command(name="lockdown", description="Lock the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lockdown(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 Channel is now under lockdown.")

    @app_commands.command(name="unlock", description="Unlock the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Channel has been unlocked.")

    @app_commands.command(name="nuke", description="Delete and recreate the channel to clear all history")
    @app_commands.checks.has_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        channel = interaction.channel
        new_channel = await channel.clone(reason="Nuke")
        await new_channel.edit(position=channel.position)
        await channel.delete()
        await new_channel.send("☢️ Channel Nuked.")

async def setup(bot):
    await bot.add_cog(ServerTools(bot))