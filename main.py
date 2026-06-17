import os
import asyncio
import discord
from discord.ext import commands
from quart import Quart, render_template, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient

class EnderBot(commands.Bot):
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    async def setup_hook(self):
        try:
            await self.load_extension("cogs.settings")
            print("Successfully loaded extension: cogs.settings")
        except Exception as e:
            print(f"Failed to load extension cogs.settings: {e}")

app = Quart(__name__)
app.config["PROVIDE_AUTOMATIC_OPTIONS"] = True

TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 5000))
# Replace with your actual application client ID from Discord Developer Portal
CLIENT_ID = os.getenv("CLIENT_ID", "123456789012345678") 

if not TOKEN or not MONGO_URI:
    raise ValueError("CRITICAL ERROR: Missing DISCORD_TOKEN or MONGO_URI environment variables.")

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ender_bot_db"]

intents = discord.Intents.default()
intents.message_content = True
bot = EnderBot(db=db, command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot Instance Online: {bot.user.name}")

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context):
    await ctx.send("🔄 Synchronizing application tree commands...")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Successfully synchronized {len(synced)} global slash commands!")
    except Exception as e:
        await ctx.send(f"❌ Synchronization failed: `{e}`")


# ==============================================================================
# QUART WEB ROUTES
# ==============================================================================

@app.route("/")
async def index():
    """1. Public Landing Page with login options and stats"""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    stats = {
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds if g.member_count)
    }
    return await render_template("index.html", invite_url=invite_url, stats=stats)


@app.route("/dashboard", methods=["GET"])
async def dashboard_hub():
    """2. Dashboard Hub: Displays server lists and actions"""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    
    # Mocking user data until full OAuth2 integration is completed
    # For testing: This maps out mock user servers to show layout buttons
    user_servers = [
        {"id": 123456789, "name": "Ender's Test Zone", "icon": None},
        {"id": 987654321, "name": "Community Safehouse", "icon": None},
        {"id": 555666777, "name": "Developer Sandbox Server", "icon": None},
    ]

    # Check which servers the bot is actively present in
    processed_servers = []
    for s in user_servers:
        bot_present = bot.get_guild(s["id"]) is not None
        processed_servers.append({
            "id": s["id"],
            "name": s["name"],
            "bot_in_guild": bot_present
        })

    return await render_template("dashboard_hub.html", servers=processed_servers, invite_url=invite_url)


@app.route("/dashboard/<int:guild_id>", methods=["GET"])
async def guild_management(guild_id):
    """3. Specific Server Configuration View"""
    guild_config = await db.settings.find_one({"guild_id": guild_id})
    prefix = guild_config.get("prefix", "!") if guild_config else "!"
    
    guild = bot.get_guild(guild_id)
    guild_name = guild.name if guild else f"Discord Server ID: ({guild_id})"

    return await render_template("dashboard.html", guild_id=guild_id, guild_name=guild_name, prefix=prefix)


@app.route("/api/settings/<int:guild_id>", methods=["POST"])
async def update_settings(guild_id):
    data = await request.get_json()
    new_prefix = data.get("prefix")

    if not new_prefix or len(new_prefix) > 5:
        return jsonify({"error": "Invalid prefix layout provided."}), 400

    await db.settings.update_one({"guild_id": guild_id}, {"$set": {"prefix": new_prefix}}, upsert=True)
    
    guild = bot.get_guild(guild_id)
    if guild and guild.system_channel:
        try:
            await guild.system_channel.send(f"⚙️ **Configuration Alert:** Prefix updated via Web Dashboard to `{new_prefix}`")
        except discord.Forbidden:
            pass

    return jsonify({"success": True, "new_prefix": new_prefix})


@app.before_serving
async def start_bot_task():
    asyncio.create_task(bot.start(TOKEN))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)