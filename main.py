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
        self.db = db  # Sharing the MongoDB connection pool

    async def setup_hook(self):
        """Executed before the bot connects to Discord; loads the settings extension."""
        try:
            await self.load_extension("cogs.settings")
            print("Successfully loaded extension: cogs.settings")
        except Exception as e:
            print(f"Failed to load extension cogs.settings: {e}")

# Setup Quart Web Application
app = Quart(__name__)
# Fix for underlying Flask configuration requirements
app.config["PROVIDE_AUTOMATIC_OPTIONS"] = True

# Fetch variables from Environment
TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 5000))
CLIENT_ID = os.getenv("CLIENT_ID") 

# Safety check for critical configuration variables
if not TOKEN or not MONGO_URI or not CLIENT_ID:
    raise ValueError(
        "CRITICAL ERROR: Missing configuration keys! "
        "Ensure DISCORD_TOKEN, MONGO_URI, and CLIENT_ID are added to Render's Environment Variables."
    )

# Initialize Asynchronous MongoDB Client via Motor
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ender_bot_db"]

# Setup Discord Bot Client Configuration
intents = discord.Intents.default()
intents.message_content = True  # Allows bot to read standard message prefix commands
bot = EnderBot(db=db, command_prefix="!", intents=intents)


# ==============================================================================
# 2. DISCORD APPLICATION EVENTS & TREE MAINTENANCE
# ==============================================================================

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"🤖 Bot Instance Online: {bot.user.name} ({bot.user.id})")
    print(f"🪐 Connected to MongoDB Database.")
    print(f"========================================")

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context):
    """
    Owner-only maintenance command. Type '!sync' in your Discord chat 
    to force clear/refresh old slash commands or register new ones.
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
    """1. Public Landing Page featuring public stats and invite routes."""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    stats = {
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds if g.member_count)
    }
    return await render_template("index.html", invite_url=invite_url, stats=stats)


@app.route("/dashboard", methods=["GET"])
async def dashboard_hub():
    """2. Dashboard Server Selection Hub. Iterates and maps join requirements."""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    
    # Placeholder array simulating user-owned admin servers.
    # Replace these IDs with your actual test server IDs to test the visual difference!
    user_servers = [
        {"id": 123456789, "name": "Ender's Test Zone"},
        {"id": 987654321, "name": "Community Safehouse"},
        {"id": 555666777, "name": "Developer Sandbox Server"},
    ]

    processed_servers = []
    for s in user_servers:
        # Check if the bot is actively present inside the cached guild index
        bot_present = bot.get_guild(s["id"]) is not None
        processed_servers.append({
            "id": s["id"],
            "name": s["name"],
            "bot_in_guild": bot_present
        })

    return await render_template("dashboard_hub.html", servers=processed_servers, invite_url=invite_url)


@app.route("/dashboard/<int:guild_id>", methods=["GET"])
async def guild_management(guild_id):
    """3. Specific Server Configuration View."""
    # Fetch existing document metadata, fallback to standard configuration defaults if absent
    guild_config = await db.settings.find_one({"guild_id": guild_id})
    prefix = guild_config.get("prefix", "!") if guild_config else "!"
    
    guild = bot.get_guild(guild_id)
    guild_name = guild.name if guild else f"Discord Server ID: ({guild_id})"

    return await render_template("dashboard.html", guild_id=guild_id, guild_name=guild_name, prefix=prefix)


@app.route("/api/settings/<int:guild_id>", methods=["POST"])
async def update_settings(guild_id):
    """4. Real-time API configuration processing route accessed by Web UI JavaScript."""
    data = await request.get_json()
    new_prefix = data.get("prefix")

    if not new_prefix or len(new_prefix) > 5:
        return jsonify({"error": "Invalid prefix configuration payload received."}), 400

    # Persist data synchronously to shared cluster collections
    await db.settings.update_one(
        {"guild_id": guild_id},
        {"$set": {"prefix": new_prefix}},
        upsert=True
    )
    
    # Broadcast configuration changes instantly to matching server chat channels
    guild = bot.get_guild(guild_id)
    if guild and guild.system_channel:
        try:
            await guild.system_channel.send(f"⚙️ **Configuration Alert:** The command prefix was changed from the Web Dashboard to `{new_prefix}`")
        except discord.Forbidden:
            pass  # Fail safely if bot lacks message permissions in that channel

    return jsonify({"success": True, "new_prefix": new_prefix})


# ==============================================================================
# 4. LIFECYCLE MANAGEMENT ASYNCIO EXECUTION BLOCK
# ==============================================================================

@app.before_serving
async def start_bot_task():
    """Hooks the Discord connection context thread execution loop directly inside Quart's runner scope."""
    asyncio.create_task(bot.start(TOKEN))

if __name__ == "__main__":
    # Hypercorn ASGI engine processes the port constraints dynamically for Render web instances.
    app.run(host="0.0.0.0", port=PORT)