import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "welcome_settings.json"
        # 🔒 LOCK TO YOUR SERVER ID
        self.MY_GUILD_ID = 1503037186034110595 

    def save_channel(self, guild_id, channel_id):
        data = {}
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                data = json.load(f)
        data[str(guild_id)] = channel_id
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def load_channel(self, guild_id):
        if not os.path.exists(self.db_path):
            return None
        with open(self.db_path, "r") as f:
            data = json.load(f)
        return data.get(str(guild_id))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Only trigger for KiteCloud server
        if member.guild.id != self.MY_GUILD_ID:
            return

        channel_id = self.load_channel(member.guild.id)
        if not channel_id:
            return

        channel = member.guild.get_channel(int(channel_id))
        if channel:
            # Your custom message formatting
            welcome_text = (
                f"**Welcome to ****KiteCloud****🪁, {member.mention}! \n\n"
                "You’ve just landed at KiteCloud. We’re building the fastest hosting community on Discord, "
                "and we're glad you're part of the deploy.\n\n"
                "🔹 🗨️**Introduce yourself:** <#1503356981040250961> (chill-chat)\n" # Replace IDs as needed
                "🔹 💁‍♂️**Get Support:** <#1503356982042562682> (support)\n"
                "🔹 👍**The Protocols:** <#1503356946311549070> (protocols)\n"
                "🔹 **Changelog:** <#1503356953638993971> (news)\n\n"
                "Feel free to ping our staff if you have any questions.** **Happy hosting!**"
            )

            embed = discord.Embed(
                title="🛰️ New Deployment Detected!",
                description=welcome_text,
                color=discord.Color.from_rgb(0, 150, 255) # KiteCloud Blue
            )
            
            # Using your previous banner link or a server icon
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_image(url="https://cdn.discordapp.com/attachments/1340943454934667345/1340943454934667345/image_449024.jpg")
            embed.set_footer(text=f"KiteCloud Resident #{member.guild.member_count}")
            
            await channel.send(content=f"Welcome {member.mention}!", embed=embed)

    @app_commands.command(name="set_welcome", description="📍 Set the KiteCloud welcome channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild.id != self.MY_GUILD_ID:
            return await interaction.response.send_message("❌ Error: Restricted to KiteCloud server.", ephemeral=True)

        self.save_channel(interaction.guild.id, channel.id)
        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))