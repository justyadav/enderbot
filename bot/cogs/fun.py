import discord
from discord import app_commands
from discord.ext import commands
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        embed = discord.Embed(title="🎱 The Magic 8-Ball", color=discord.Color.purple())
        embed.add_field(name="Question:", value=question, inline=False)
        embed.add_field(name="Answer:", value=random.choice(responses), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roll", description="Roll a dice (e.g., 6, 20, 100 sides)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        result = random.randint(1, sides)
        await interaction.response.send_message(f"🎲 You rolled a **{result}** on a {sides}-sided die!")

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        outcome = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on: **{outcome}**!")

    @app_commands.command(name="meme", description="Get a random (simulated) meme description")
    async def meme(self, interaction: discord.Interaction):
        # In a 100+ cmd bot, you'd usually use an API here, 
        # but for now, let's add a few hardcoded ones to the count!
        memes = ["Distracted Boyfriend", "Woman Yelling at a Cat", "Drake Hotline Bling"]
        await interaction.response.send_message(f"🖼️ Random Meme Idea: **{random.choice(memes)}**")

async def setup(bot):
    await bot.add_cog(Fun(bot)) 