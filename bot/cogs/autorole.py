import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "autorole_settings.json"

    def load_role(self, guild_id):
        """Load the stored role ID for a specific server."""
        if not os.path.exists(self.db_path):
            return None
        with open(self.db_path, "r") as f:
            data = json.load(f)
        return data.get(str(guild_id))

    def save_role(self, guild_id, role_id):
        """Save the role ID for a specific server."""
        data = {}
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                data = json.load(f)
        
        data[str(guild_id)] = role_id
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Automatically assigns the role when a member joins."""
        role_id = self.load_role(member.guild.id)
        if not role_id:
            return

        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
                print(f"✅ Assigned {role.name} to {member.name}")
            except discord.Forbidden:
                print(f"❌ Permission denied to assign role in {member.guild.name}")

    @app_commands.command(name="set_autorole", description="⚙️ Set the role given to new members automatically")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_autorole(self, interaction: discord.Interaction, role: discord.Role):
        """Admin command to set the autorole."""
        # Check if the bot's role is high enough
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message(
                "❌ **Error:** That role is higher than my own role! Drag my role above it in Server Settings.",
                ephemeral=True
            )

        self.save_role(interaction.guild.id, role.id)
        
        embed = discord.Embed(
            title="✅ Autorole Updated",
            description=f"New members will now automatically receive the {role.mention} role.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))