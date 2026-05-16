import discord
from discord import app_commands
from discord.ext import commands

class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Replace the URL with your actual Discord Server Invite Link
        self.add_item(discord.ui.Button(label="Join Support Server", url="https://discord.gg/pj9bqcYuEY", style=discord.ButtonStyle.link))

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="support", description="Get an invite to the bot's official support server")
    async def support(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🆘 Need Help?",
            description=(
                "If you're experiencing issues, found a bug, or have suggestions, "
                "join our official support server! Our team is ready to help."
            ),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="What we offer:", value="• Bug Reporting\n• Feature Suggestions\n• Technical Support", inline=False)
        
        await interaction.response.send_message(embed=embed, view=SupportView())

async def setup(bot):
    await bot.add_cog(Support(bot))