import discord
from discord import app_commands
from discord.ext import commands
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
import os
import re
import asyncio

SETTINGS_FILE = "automod_settings.json"
WARN_TRACKER_FILE = "warn_tracker.json"

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def save_json(filepath, data):
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
    except OSError as e:
        print(f"Failed to save {filepath}: {e}")

class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = load_json(SETTINGS_FILE)
        self.warn_tracker = load_json(WARN_TRACKER_FILE)
        
        # Spam tracking: {guild_id: {user_id: [datetime objects]}}
        self.spam_tracker = defaultdict(lambda: defaultdict(list))
        
        # Default global bad words
        self.bad_words = [
            "nazi", "retard", "faggot", "slut", "whore", 
            "rape", "nigga", "nigger", "porn", "hentai"
        ]

        # Start background cleanup
        self.bot.loop.create_task(self._cleanup_spam_loop())

    # ─── HELPERS ───────────────────────────────────────────

    def _gid(self, guild_id: int) -> str:
        return str(guild_id)

    def _uid(self, user_id: int) -> str:
        return str(user_id)

    def _get_cfg(self, guild_id: int) -> dict:
        gid = self._gid(guild_id)
        if gid not in self.settings:
            self.settings[gid] = {
                "anti_link": False,
                "anti_invites": False,
                "anti_spam": False,
                "spam_threshold": 5,
                "spam_window": 5,
                "anti_bad_words": True,
                "anti_caps": False,
                "caps_percentage": 70,
                "caps_min_length": 10,
                "anti_repeat": False,
                "repeat_threshold": 5,
                "anti_mass_mention": False,
                "mass_mention_threshold": 5,
                "auto_warn": True,
                "warn_limit": 3,
                "warn_action": "mute",
                "mute_duration": 10,
                "log_channel": None,
                "ignored_roles": [],
                "ignored_channels": [],
                "filtered_words": []
            }
            save_json(SETTINGS_FILE, self.settings)
        return self.settings[gid]

    async def _cleanup_spam_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(60)
            now = datetime.now(timezone.utc)
            for gid in list(self.spam_tracker.keys()):
                for uid in list(self.spam_tracker[gid].keys()):
                    self.spam_tracker[gid][uid] = [
                        t for t in self.spam_tracker[gid][uid]
                        if t > now - timedelta(seconds=60)
                    ]
                    if not self.spam_tracker[gid][uid]:
                        del self.spam_tracker[gid][uid]

    async def _log(self, guild: discord.Guild, action: str, user: discord.Member, reason: str, message: discord.Message = None):
        cfg = self._get_cfg(guild.id)
        log_id = cfg.get("log_channel")
        if not log_id:
            return
        
        channel = guild.get_channel(log_id)
        if not channel:
            return

        embed = discord.Embed(
            title=f"🚨 AutoMod — {action}",
            description=f"**User:** {user.mention} (`{user.id}`)\n**Reason:** {reason}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        if message and message.content:
            clean_content = message.content[:1000].replace("`", "")
            embed.add_field(name="Message", value=f"```\n{clean_content}\n```", inline=False)
        
        try:
            await channel.send(embed=embed)
        except:
            pass

    # ─── ACTIONS ───────────────────────────────────────────

    async def _take_action(self, guild: discord.Guild, user: discord.Member, reason: str):
        cfg = self._get_cfg(guild.id)
        action = cfg.get("warn_action", "mute")
        duration = cfg.get("mute_duration", 10)

        try:
            if action == "mute":
                until = discord.utils.utcnow() + timedelta(minutes=duration)
                await user.timeout(until, reason=reason)
            elif action == "kick":
                await user.kick(reason=reason)
            elif action == "ban":
                await user.ban(reason=reason, delete_message_days=1)
        except discord.Forbidden:
            await self._log(guild, "Error", user, f"Failed to {action}: Missing Permissions")

    async def handle_infraction(self, message: discord.Message, reason: str):
        guild = message.guild
        author = message.author
        cfg = self._get_cfg(guild.id)

        try:
            await message.delete()
        except:
            pass

        gid, uid = self._gid(guild.id), self._uid(author.id)
        self.warn_tracker.setdefault(gid, {})
        self.warn_tracker[gid][uid] = self.warn_tracker[gid].get(uid, 0) + 1
        current = self.warn_tracker[gid][uid]
        limit = cfg.get("warn_limit", 3)
        save_json(WARN_TRACKER_FILE, self.warn_tracker)

        await message.channel.send(f"🚫 {author.mention}, {reason} (`{current}/{limit}`)", delete_after=5)
        await self._log(guild, "Infraction", author, reason, message)

        if current >= limit:
            await self._take_action(guild, author, f"Reached warn limit ({limit})")
            self.warn_tracker[gid][uid] = 0
            save_json(WARN_TRACKER_FILE, self.warn_tracker)

    # ─── SLASH COMMANDS ────────────────────────────────────

    automod = app_commands.Group(name="automod", description="Configure Auto-Moderation")

    @automod.command(name="status")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def status(self, itx: discord.Interaction):
        """View all automod settings."""
        cfg = self._get_cfg(itx.guild_id)
        embed = discord.Embed(title="🛡️ AutoMod Settings", color=discord.Color.blue())
        for k, v in cfg.items():
            if isinstance(v, list): v = f"{len(v)} items"
            embed.add_field(name=k.replace("_", " ").title(), value=f"`{v}`", inline=True)
        await itx.response.send_message(embed=embed)

    @automod.command(name="logchannel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_log(self, itx: discord.Interaction, channel: discord.TextChannel):
        """Set where automod alerts are sent."""
        cfg = self._get_cfg(itx.guild_id)
        cfg["log_channel"] = channel.id
        save_json(SETTINGS_FILE, self.settings)
        await itx.response.send_message(f"✅ Log channel set to {channel.mention}")

    @automod.command(name="addword")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add_word(self, itx: discord.Interaction, word: str):
        """Add a custom word to the filter."""
        cfg = self._get_cfg(itx.guild_id)
        w = word.lower().strip()
        if w not in cfg["filtered_words"]:
            cfg["filtered_words"].append(w)
            save_json(SETTINGS_FILE, self.settings)
            await itx.response.send_message(f"✅ Added `{w}` to filter.")
        else:
            await itx.response.send_message("Word already in filter.", ephemeral=True)

    @automod.command(name="links")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def toggle_links(self, itx: discord.Interaction, enabled: bool):
        """Toggle anti-link protection."""
        cfg = self._get_cfg(itx.guild_id)
        cfg["anti_link"] = enabled
        save_json(SETTINGS_FILE, self.settings)
        await itx.response.send_message(f"✅ Anti-link is now `{enabled}`")

    # ─── LISTENERS ─────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild: return
        if msg.author.guild_permissions.manage_messages: return

        cfg = self._get_cfg(msg.guild.id)
        
        # Bypass checks
        if msg.channel.id in cfg.get("ignored_channels", []): return
        if any(r.id in cfg.get("ignored_roles", []) for r in msg.author.roles): return

        content = msg.content.lower()

        # 1. Word Filter
        if cfg.get("anti_bad_words"):
            checks = self.bad_words + cfg.get("filtered_words", [])
            if any(w in content for w in checks):
                return await self.handle_infraction(msg, "Blacklisted word")

        # 2. Links & Invites
        if cfg.get("anti_invites") and ("discord.gg/" in content or "discord.com/invite/" in content):
            return await self.handle_infraction(msg, "Invites are not allowed")
        
        if cfg.get("anti_link") and re.search(r"https?://", content):
            return await self.handle_infraction(msg, "Links are not allowed")

        # 3. Spam
        if cfg.get("anti_spam"):
            now = datetime.now(timezone.utc)
            gid, uid = msg.guild.id, msg.author.id
            self.spam_tracker[gid][uid].append(now)
            
            # Filter messages in window
            window = cfg.get("spam_window", 5)
            self.spam_tracker[gid][uid] = [t for t in self.spam_tracker[gid][uid] if t > now - timedelta(seconds=window)]
            
            if len(self.spam_tracker[gid][uid]) >= cfg.get("spam_threshold", 5):
                return await self.handle_infraction(msg, "Spamming")

        # 4. Caps
        if cfg.get("anti_caps") and len(msg.content) >= cfg.get("caps_min_length", 10):
            alphas = [c for c in msg.content if c.isalpha()]
            if alphas:
                ratio = (sum(1 for c in alphas if c.isupper()) / len(alphas)) * 100
                if ratio > cfg.get("caps_percentage", 70):
                    return await self.handle_infraction(msg, "Excessive Caps")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.on_message(after)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))