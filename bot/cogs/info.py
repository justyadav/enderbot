import discord
from discord import app_commands
from discord.ext import commands
import platform

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whois", description="Deep dive into a user's permissions and status")
    async def whois(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        roles = [role.mention for role in member.roles[1:]] # Skip @everyone
        
        embed = discord.Embed(title=f"User Lookup: {member.name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, 'R'))
        embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, 'R'))
        embed.add_field(name="Top Role", value=member.top_role.mention)
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="permissions", description="Check a user's permissions in this channel")
    async def perms(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        permissions = interaction.channel.permissions_for(member)
        # Filtering for only the 'True' permissions
        valid_perms = [p[0].replace('_', ' ').title() for p in permissions if p[1]]
        
        embed = discord.Embed(
            title=f"Permissions for {member.name}", 
            description=", ".join(valid_perms) if valid_perms else "No permissions", 
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))