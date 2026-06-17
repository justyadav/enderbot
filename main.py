import os
import asyncio
import discord
from discord.ext import commands
from quart import Quart, render_template, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient

# ==============================================================================
# 1. INITIALIZATION & CUSTOM BOT CLASS
# ==============================================================================

class EnderBot(commands.Bot):
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db  # Sharing the MongoDB connection pool across the application

    async def setup_hook(self):
        """Executed before the bot connects to Discord; perfect for loading cogs."""
        try:
            await self.load_extension("cogs.settings")
            print("Successfully loaded extension: cogs.settings")
        except Exception as e:
            print(f"Failed to load extension cogs.settings: {e}")

# Setup Quart Web Application
app = Quart(__name__)
# Crucial fix for Flask/Quart breaking compatibility change:
app.config["PROVIDE_AUTOMATIC_OPTIONS"] = True

# Fetch variables from Environment
TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN or not MONGO_URI:
    raise ValueError("CRITICAL ERROR: Missing DISCORD_TOKEN or MONGO_URI environment variables.")

# Initialize Asynchronous MongoDB Client via Motor
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ender_bot_db"]

# Setup Discord Bot Client Configuration
intents = discord.Intents.default()
intents.message_content = True  # Required for reading prefix commands in chat
bot = EnderBot(db=db, command_prefix="!", intents=intents)


# ==============================================================================
# 2. DISCORD APPLICATION EVENTS & SYNC COMMANDS
# ==============================================================================

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"🤖 Bot Instance Online: {bot.user.name} ({bot.user.id})")
    print(f"🪐 Connected to MongoDB Successfully.")
    print(f"========================================")

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context):
    """
    Owner-only maintenance command to clean up / register application slash commands.
    Type '!sync' in your Discord chat to update old or newly updated slash commands.
    """
    await ctx.send("🔄 Synchronizing application tree commands... please wait.")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Successfully synchronized {len(synced)} global slash commands with Discord!")
    except Exception as e:
        await ctx.send(f"❌ Synchronization failed: `{e}`")


# ==============================================================================
# 3. QUART WEB DASHBOARD PANEL ROUTES
# ==============================================================================

@app.route("/")
async def index():
    """Root Route confirming web operations work cleanly on Render."""
    return "Ender Bot Web Dashboard is Online!"

@app.route("/dashboard/<int:guild_id>", methods=["GET"])
async def dashboard(guild_id):
    """Fetches configuration from MongoDB and presents the HTML panel state."""
    # Find guild settings in Mongo, fallback to default "!" if configuration doesn't exist yet
    guild_config = await db.settings.find_one({"guild_id": guild_id})
    prefix = guild_config.get("prefix", "!") if guild_config else "!"
    
    # Optional metadata pull if bot shares memory cache space with targeted guild
    guild = bot.get_guild(guild_id)
    guild_name = guild.name if guild else f"Discord Server ID: ({guild_id})"

    return await render_template("dashboard.html", guild_id=guild_id, guild_name=guild_name, prefix=prefix)

@app.route("/api/settings/<int:guild_id>", methods=["POST"])
async def update_settings(guild_id):
    """API Endpoint consumed by the HTML front-end via JS Fetch to update values dynamically."""
    data = await request.get_json()
    new_prefix = data.get("prefix")

    if not new_prefix or len(new_prefix) > 5:
        return jsonify({"error": "Invalid prefix layout provided (Must be 1-5 characters)."}), 400

    # Write change directly to MongoDB Atlas instance
    await db.settings.update_one(
        {"guild_id": guild_id},
        {"$set": {"prefix": new_prefix}},
        upsert=True
    )
    
    # Instantly dispatch interactive chat visual feedback alerting of configuration change
    guild = bot.get_guild(guild_id)
    if guild and guild.system_channel:
        try:
            await guild.system_channel.send(f"⚙️ **Configuration Alert:** The command prefix was changed from the Web Dashboard to `{new_prefix}`")
        except discord.Forbidden:
            pass  # Fail gracefully if bot doesn't possess view/write permissions in system channel

    return jsonify({"success": True, "new_prefix": new_prefix})


# ==============================================================================
# 4. LIFECYCLE MANAGEMENT RUNNER BLOCK
# ==============================================================================

@app.before_serving
async def start_bot_task():
    """Ties Discord client bot authorization loop right into Quart's native asyncio startup loop."""
    asyncio.create_task(bot.start(TOKEN))

if __name__ == "__main__":
    # Hypercorn engine runs on 0.0.0.0 and dynamically binds to the environment variable PORT requested by Render.
    app.run(host="0.0.0.0", port=PORT)