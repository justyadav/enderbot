import os
import asyncio
import discord
from discord.ext import commands
from quart import Quart, render_template, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Initialization and Configurations
class EnderBot(commands.Bot):
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db  # Sharing database connection

    async def setup_hook(self):
        # Load cogs extension
        await self.load_extension("cogs.settings")
        print("Bot extensions loaded successfully.")

# Setup Quart App
app = Quart(__name__)

# Fetch environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN or not MONGO_URI:
    raise ValueError("Missing critical environment variables (DISCORD_TOKEN or MONGO_URI)")

# Database Setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ender_bot_db"]

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = EnderBot(db=db, command_prefix="!", intents=intents)


# 2. Web Dashboard Routes
@app.route("/")
async def index():
    return "Ender Bot Web Dashboard is Online!"

@app.route("/dashboard/<int:guild_id>", methods=["GET"])
async def dashboard(guild_id):
    # Fetch current setting from MongoDB
    guild_config = await db.settings.find_one({"guild_id": guild_id})
    prefix = guild_config.get("prefix", "!") if guild_config else "!"
    
    # Check if bot is in the guild to fetch live data
    guild = bot.get_guild(guild_id)
    guild_name = guild.name if guild else f"Guild ({guild_id})"

    return await render_template("dashboard.html", guild_id=guild_id, guild_name=guild_name, prefix=prefix)

@app.route("/api/settings/<int:guild_id>", methods=["POST"])
async def update_settings(guild_id):
    """API endpoint to update settings via Web Panel"""
    data = await request.get_json()
    new_prefix = data.get("prefix")

    if not new_prefix:
        return jsonify({"error": "Invalid prefix"}), 400

    # Upsert data to MongoDB
    await db.settings.update_one(
        {"guild_id": guild_id},
        {"$set": {"prefix": new_prefix}},
        upsert=True
    )
    
    # Dynamic live reaction: notify a channel in the guild if available
    guild = bot.get_guild(guild_id)
    if guild and guild.system_channel:
        try:
            await guild.system_channel.send(f"⚙️ **System:** Command prefix updated via Web Dashboard to `{new_prefix}`")
        except discord.Forbidden:
            pass

    return jsonify({"success": True, "new_prefix": new_prefix})


# 3. Combined Runner Logic
@app.before_serving
async def start_bot():
    # Hook bot startup into Quart's event loop startup lifecycle
    asyncio.create_task(bot.start(TOKEN))

if __name__ == "__main__":
    # Hypercorn is Quart's default ASGI server. 
    # Binding to 0.0.0.0 and using the dynamic PORT environment variable satisfies Render.
    app.run(host="0.0.0.0", port=PORT)