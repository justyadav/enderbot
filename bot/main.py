import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

from cogs.gladbyte_tickets import GladbyteView, TicketControls, load_settings

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class EnderBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("--- 🚀 Initializing Ender Bot ---")

        # 1. Load cogs FIRST
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != "__init__.py":
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Loaded Cog: {filename}')
                except Exception as e:
                    print(f'❌ Error loading {filename}: {e}')

        # 2. Register persistent views
        self.add_view(TicketControls())
        
        settings = load_settings()
        if settings:
            for guild_id_str, cat_id in settings.items():
                self.add_view(GladbyteView(category_id=cat_id))
                print(f'✅ Registered: GladbyteView for guild {guild_id_str}')
        else:
            self.add_view(GladbyteView(category_id=None))

        # 3. GLOBAL SYNC ONLY
        # This ensures commands are the same everywhere and don't duplicate
        await self.tree.sync()
        print("🌍 Slash Commands Synced Globally")

    async def on_ready(self):
        # --- START OF CLEANUP SECTION (Delete this after running once) ---
        # Replace this with your actual Server ID
        GLADBYTE_GUILD_ID = 1340943454934667345 
        guild = discord.Object(id=GLADBYTE_GUILD_ID)
        
        # This removes commands that were synced specifically to your server
        self.tree.clear_commands(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"🧹 Cleared guild-specific commands for {GLADBYTE_GUILD_ID}")
        # --- END OF CLEANUP SECTION ---

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Yaduvanshi1816_ |/help"
        )
        await self.change_presence(
            status=discord.Status.do_not_disturb,
            activity=activity
        )
        print(f'🔥 ender Bot is Online as {self.user}!')

bot = EnderBot()

if __name__ == "__main__":
    bot.run(TOKEN)