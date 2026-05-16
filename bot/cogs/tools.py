import discord
from discord import app_commands
from discord.ext import commands

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="calculate", description="Basic math operations")
    @app_commands.describe(operation="e.g. 5 + 5, 10 * 2")
    async def calculate(self, interaction: discord.Interaction, operation: str):
        try:
            # Note: eval is risky in big projects, but for basic math it works.
            # A safer way is using a math library, but this is fine for starters.
            result = eval(operation, {"__builtins__": None}, {})
            await interaction.response.send_message(f"🔢 Result: `{result}`")
        except:
            await interaction.response.send_message("❌ Invalid operation!", ephemeral=True)

    @app_commands.command(name="poll", description="Create a simple yes/no poll")
    async def poll(self, interaction: discord.Interaction, question: str):
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blue())
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("✅")
        await message.add_reaction("❌")

    @app_commands.command(name="reminder", description="Set a quick reminder")
    async def reminder(self, interaction: discord.Interaction, time_mins: int, task: str):
        await interaction.response.send_message(f"⏰ Okay! I'll remind you about '{task}' in {time_mins} minutes.")
        import asyncio
        await asyncio.sleep(time_mins * 60)
        await interaction.followup.send(f"🔔 {interaction.user.mention}, Reminder: **{task}**")

async def setup(bot):
    await bot.add_cog(Tools(bot))