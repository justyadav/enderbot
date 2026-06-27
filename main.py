import os
import asyncio
import logging
from contextlib import asynccontextmanager
import discord
from discord.ext import commands, tasks
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Setup Environment & Logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("EnderBot")

# =====================================================
# 🗄️ DATABASE & BOT INITIALIZATION
# =====================================================
MONGO_URI = os.getenv("MONGO_URI")
TOKEN = os.getenv("DISCORD_TOKEN")

# Global variables to pass around resources safely
db_client = None
db = None

# Discord Bot Setup with standard intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =====================================================
# 🔄 DYNAMIC STATUS LOOP TASK
# =====================================================
@tasks.loop(minutes=5)
async def update_status():
    """Background task that runs every 5 minutes to refresh bot statistics."""
    if not bot.is_ready():
        return

    # Calculate global tracking metrics across all connected servers
    total_servers = len(bot.guilds)
    total_members = sum(guild.member_count for guild in bot.guilds if guild.member_count)

    status_text = f"over {total_servers} servers | {total_members} members"
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=status_text
        )
    )
    log.info(f"🔄 Global presence updated: Watching {status_text}")       

# =====================================================
# 🚀 FASTAPI ASYNC LIFESPAN MATRIX
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    
    # 1. Boot up Motor MongoDB Connection
    log.info("Connecting to MongoDB Cluster...")
    db_client = AsyncIOMotorClient(MONGO_URI)
    db = db_client["discord_bot_db"]
    
    # 2. Inject DB reference directly into the bot instance
    bot.db = db
    
    # 3. Load your Cogs array asynchronously
    extensions = [
        'cogs.moderation', 'cogs.mod_utils', 'cogs.config', 
        'cogs.help', 'cogs.music', 'cogs.logging', 
        'cogs.autorole', 'cogs.general'
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            log.info(f"Loaded extension: {ext}")
        except Exception as e:
            log.error(f"Failed to load extension {ext}: {e}")

    # Start presence loops
    update_status.start()

    # 4. Launch the Discord Bot client loop task
    bot_task = asyncio.create_task(bot.start(TOKEN))
    log.info("Discord Bot background thread running.")
    
    yield # --- FastAPI runs here while background loops spin ---
    
    # 5. Shutdown Routine
    log.info("System shutdown triggered. Safely closing connection paths...")
    update_status.cancel()
    await bot.close()
    db_client.close()
    bot_task.cancel()

# =====================================================
# 📡 APPLICATION INSTANTIATION & TEMPLATES
# =====================================================
# Fixed: Initialized before routes use decorators
app = FastAPI(lifespan=lifespan, title="Ender Bot v2 Core API")
templates = Jinja2Templates(directory="templates")

# =====================================================
# 🌐 WEB API & DASHBOARD ENDPOINTS
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Renders a live HTML dashboard reading directly from the active Discord connection."""
    if not bot.is_ready():
        return "<h1>Ender Bot is compiling network matrix structures. Refresh in 5 seconds...</h1>"

    # Gather data from the live client cache arrays
    guilds_data = []
    total_users = 0
    
    for guild in bot.guilds:
        total_users += guild.member_count if guild.member_count else 0
        guilds_data.append({
            "name": guild.name,
            "id": guild.id,
            "member_count": guild.member_count
        })

    # Render data straight into your Jinja2 template frame
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "bot_name": bot.user.name,
        "latency": round(bot.latency * 1000),
        "server_count": len(bot.guilds),
        "user_count": total_users,
        "guilds": guilds_data
    })

@app.get("/api/status")
async def json_api_status():
    """Alternative JSON endpoint for health checks and integrations."""
    return {
        "status": "online",
        "bot_latency_ms": round(bot.latency * 1000) if bot.is_ready() else "offline",
        "cached_guilds_count": len(bot.guilds) if bot.is_ready() else 0
    }

@app.get("/api/guild/{guild_id}/stats")
async def get_guild_data(guild_id: int):
    """API reading live from both Discord and your MongoDB cache simultaneously."""
    if not bot.is_ready():
        return {"error": "Discord client is initializing"}
        
    guild = bot.get_guild(guild_id)
    if not guild:
        return {"error": "Guild not found by bot instance"}
        
    config = await bot.db["guild_settings"].find_one({"guild_id": guild_id}) or {}
    
    return {
        "name": guild.name,
        "member_count": guild.member_count,
        "anti_invite_filter": config.get("anti_invite", True),
        "anti_link_filter": config.get("anti_link", False)
    }

# =====================================================
# ⚙️ DISCORD GATEWAY EVENTS
# =====================================================
@bot.event
async def on_ready():
    log.info(f"🟩 Discord Session established as: {bot.user.name} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        log.info(f"🔄 Global tree synchronization complete. Synced {len(synced)} slash commands.")
    except Exception as e:
        log.error(f"❌ Failed to sync app tree commands: {e}")

# =====================================================
# 🔌 EXECUTION ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    # Pterodactyl often passes the assigned port via 'SERVER_PORT' instead of 'PORT'
    # This fallback sequence checks both before defaulting to 8080
    allocated_port = os.getenv("SERVER_PORT") or os.getenv("PORT")
    port = int(allocated_port) if allocated_port else 8080
    
    # Check if the panel provided a specific internal bind IP
    bind_host = os.getenv("SERVER_IP", "0.0.0.0")

    log.info(f"🚀 Launching FastAPI Web Infrastructure on {bind_host}:{port}")
    
    uvicorn.run(
        "main:app", 
        host=bind_host, 
        port=port, 
        log_level="info"
    )
