import discord
from discord import app_commands
from discord.ext import commands

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invites", description="Check how many users someone has invited")
    @app_commands.describe(member="The member whose invites you want to check")
    async def check_invites(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        # Get all invites for the guild
        invites = await interaction.guild.invites()
        
        total_invites = 0
        for invite in invites:
            if invite.inviter and invite.inviter.id == member.id:
                total_invites += invite.uses

        embed = discord.Embed(
            title=f"✉️ Invite Stats: {member.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Total Invites", value=f"**{total_invites}** users", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invite_leaderboard", description="Show the top recruiters in the server")
    async def invite_lb(self, interaction: discord.Interaction):
        await interaction.response.defer() # Fetching invites can be slow in big servers
        
        invites = await interaction.guild.invites()
        invite_counts = {}

        for invite in invites:
            if invite.inviter:
                inviter_name = invite.inviter.name
                invite_counts[inviter_name] = invite_counts.get(inviter_name, 0) + invite.uses

        # Sort by most uses
        sorted_invites = sorted(invite_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        
        if not sorted_invites:
            return await interaction.followup.send("No active invites found with uses.")

        lb_description = ""
        for i, (name, count) in enumerate(sorted_invites, 1):
            lb_description += f"**{i}. {name}** — {count} invites\n"

        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} Top Recruiters",
            description=lb_description,
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))