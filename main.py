import os
import asyncio
import aiohttp
import discord
from discord.ext import commands
from quart import Quart, render_template, request, jsonify, redirect, url_for, session
from motor.motor_asyncio import AsyncIOMotorClient

# ==============================================================================
# 1. INITIALIZATION & APP CONFIGURATION
# ==============================================================================

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
# A secure secret key is required to use signed browser cookies ('session')
app.secret_key = os.getenv("SECRET_KEY", "ender_bot_super_secret_session_key_123!")

# Fetch Environment Variables
TOKEN = os.getenv("DISCORD_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN or not MONGO_URI or not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(
        "CRITICAL ERROR: Missing configuration keys! "
        "Ensure DISCORD_TOKEN, MONGO_URI, CLIENT_SECRET, and CLIENT_ID are added to Render's Environment Variables."
    )

# Setup Database & Bot
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ender_bot_db"]

intents = discord.Intents.default()
intents.message_content = True
bot = EnderBot(db=db, command_prefix="!", intents=intents)

# Global API endpoints for Discord OAuth2
DISCORD_API_URL = "https://discord.com/api/v10"


# ==============================================================================
# 2. DISCORD AUTHENTICATION & ROUTING LOGIC
# ==============================================================================

@app.route("/")
async def index():
    """Public Landing Page featuring dynamic server and tracking statistics."""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    stats = {
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds if g.member_count)
    }
    return await render_template("index.html", invite_url=invite_url, stats=stats, logged_in="user" in session)


@app.route("/login")
async def login():
    """Redirects the client browser directly to Discord's secure authorization screen."""
    # Build your exact redirect URI based on whether you are running locally or live on Render
    root_url = request.host_url.replace("http://", "https://") if "onrender.com" in request.host else request.host_url
    redirect_uri = f"{root_url}login/callback".rstrip("/")
    
    # Requesting identity to see user details and guilds to read server management states
    discord_login_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={encode_uri(redirect_uri)}&response_type=code&scope=identify%20guilds"
    )
    return redirect(discord_login_url)


@app.route("/login/callback")
async def login_callback():
    """Receives the access code from Discord and swaps it for an authenticated User Token."""
    code = request.args.get("code")
    if not code:
        return "Authentication cancelled or missing authorization code code.", 400

    root_url = request.host_url.replace("http://", "https://") if "onrender.com" in request.host else request.host_url
    redirect_uri = f"{root_url}login/callback".rstrip("/")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as client_session:
        # 1. Swap authorization code for an API access token token
        async with client_session.post(f"{DISCORD_API_URL}/oauth2/token", data=data, headers=headers) as resp:
            token_data = await resp.get_json()
            access_token = token_data.get("access_token")
            
        if not access_token:
            return "Failed to retrieve access configurations from Discord backend.", 400

        # 2. Fetch authenticated profile data mapping who logged in
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        async with client_session.get(f"{DISCORD_API_URL}/users/@me", headers=auth_headers) as resp:
            user_info = await resp.get_json()

        # 3. Fetch all servers the logged-in user belongs to
        async with client_session.get(f"{DISCORD_API_URL}/users/@me/guilds", headers=auth_headers) as resp:
            user_guilds = await resp.get_json()

    # Save details safely inside encrypted browser session memory
    session["user"] = user_info
    session["user_guilds"] = user_guilds

    return redirect(url_for("dashboard_hub"))


@app.route("/logout")
async def logout():
    """Clears the browser session logs completely."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard", methods=["GET"])
async def dashboard_hub():
    """2. Dashboard Hub: Automatically processes and displays the logged-in user's server list."""
    if "user" not in session:
        return redirect(url_for("login"))

    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    user_guilds = session.get("user_guilds", [])
    
    processed_servers = []
    for g in user_guilds:
        # Filter: Only show servers where the user is either the Owner OR has Manage Server permissions (0x20)
        permissions = int(g.get("permissions", 0))
        is_admin = (permissions & 0x8) == 0x8 or (permissions & 0x20) == 0x20 or g.get("owner", False)
        
        if is_admin:
            guild_id = int(g["id"])
            # Auto-check if Ender bot is actively present inside this server right now
            bot_present = bot.get_guild(guild_id) is not None
            
            processed_servers.append({
                "id": guild_id,
                "name": g["name"],
                "bot_in_guild": bot_present
            })

    return await render_template("dashboard_hub.html", servers=processed_servers, invite_url=invite_url, user=session["user"])


# ==============================================================================
# 3. INDIVIDUAL GUILD PANELS & RUNNER Lifecycles
# ==============================================================================

@app.route("/dashboard/<int:guild_id>", methods=["GET"])
async def guild_management(guild_id):
    """3. Specific Server Configuration View."""
    if "user" not in session:
        return redirect(url_for("login"))

    # Security Guard: Verify the user actually has access to manage this server ID
    user_guilds = session.get("user_guilds", [])
    if not any(int(g["id"]) == guild_id for g in user_guilds):
        return "Access Denied: You do not have permissions to manage this guild.", 403

    guild_config = await db.settings.find_one({"guild_id": guild_id})
    prefix = guild_config.get("prefix", "!") if guild_config else "!"
    
    guild = bot.get_guild(guild_id)
    guild_name = guild.name if guild else f"Discord Server ID: ({guild_id})"

    return await render_template("dashboard.html", guild_id=guild_id, guild_name=guild_name, prefix=prefix)


@app.route("/api/settings/<int:guild_id>", methods=["POST"])
async def update_settings(guild_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized context access"}), 401

    data = await request.get_json()
    new_prefix = data.get("prefix")

    if not new_prefix or len(new_prefix) > 5:
        return jsonify({"error": "Invalid prefix configuration payload received."}), 400

    await db.settings.update_one({"guild_id": guild_id}, {"$set": {"prefix": new_prefix}}, upsert=True)
    
    guild = bot.get_guild(guild_id)
    if guild and guild.system_channel:
        try:
            await guild.system_channel.send(f"⚙️ **Configuration Alert:** Prefix updated via Web Dashboard to `{new_prefix}`")
        except discord.Forbidden:
            pass

    return jsonify({"success": True, "new_prefix": new_prefix})


def encode_uri(text):
    """Helper method to format redirect strings cleanly for Discord API."""
    import urllib.parse
    return urllib.parse.quote_plus(text)


@bot.event
async def on_ready():
    print(f"🤖 Bot Instance Online: {bot.user.name}")


@app.before_serving
async def start_bot_task():
    asyncio.create_task(bot.start(TOKEN))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)