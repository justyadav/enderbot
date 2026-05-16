import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_overview_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📋 **Ender Bot — Command Help by Yaduvanshi1816_**",
            description=(
                "Welcome to **Ender Bot**! I'm packed with moderation, utility, fun, "
                "and ticketing features.\n\n"
                "Use the **dropdown menu below** to browse commands by category, "
                "or use `/help <category>` to jump straight there.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🛡️ **Moderation** — Keep your server safe\n"
                "🤖 **AutoMod** — Automated protection & filters\n"
                "⚙️ **Configuration** — Server settings & logging\n"
                "🎫 **Tickets** — Support ticket system\n"
                "🎮 **Fun** — Games & entertainment\n"
                "ℹ️ **General** — Utility & information\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 *Commands marked with 🔒 require Manage Server or Administrator.*"
            ),
            color=discord.Color.from_rgb(88, 101, 242)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else discord.Embed.Empty)
        embed.set_footer(text="Ender Bot • Yaduvanshi1816_ • Select a category below", icon_url=self.bot.user.display_avatar.url if self.bot.user else discord.Embed.Empty)
        embed.timestamp = discord.utils.utcnow()
        return embed

    def build_category_embed(self, category: str) -> discord.Embed:
        categories = {
            "moderation": {
                "emoji": "🛡️",
                "title": "Moderation Commands",
                "color": discord.Color.red(),
                "commands": (
                    "**🔒 /ban** `<user> [reason]` — Ban a member\n"
                    "**🔒 /kick** `<user> [reason]` — Kick a member\n"
                    "**🔒 /timeout** `<user> <duration> [reason]` — Timeout a member\n"
                    "**🔒 /clear** `<amount>` — Bulk delete messages\n"
                    "**🔒 /slowmode** `<seconds>` — Set slowmode\n"
                    "**🔒 /lockdown** — Lock the current channel\n"
                    "**🔒 /nuke** — Fresh reset of the current channel\n"
                    "**🔒 /role_add** `<user> <role>` — Add a role\n"
                    "**🔒 /set_autorole** `<role>` — Auto-assign role on join\n"
                )
            },
            "automod": {
                "emoji": "🤖",
                "title": "AutoMod Configuration",
                "color": discord.Color.dark_gold(),
                "commands": (
                    "**🔒 /automod links** `<true/false>` — Toggle link blocking\n"
                    "**🔒 /automod invites** `<true/false>` — Toggle invite blocking\n"
                    "**🔒 /automod spam** `<true/false>` — Toggle spam detection\n"
                    "**🔒 /automod spamconfig** `<threshold> <window>` — Set sensitivity\n"
                    "**🔒 /automod caps** `<true/false>` — Toggle ALL-CAPS filter\n"
                    "**🔒 /automod capsconfig** `<%> <min_len>` — Set caps sensitivity\n"
                    "**🔒 /automod repeat** `<true/false>` — Toggle repeated word filter\n"
                    "**🔒 /automod mentions** `<true/false> <limit>` — Mass-mention filter\n"
                    "**🔒 /automod badwords** `<true/false>` — Toggle word filter\n"
                    "**🔒 /automod addword** `<word>` — Add custom filtered word\n"
                    "**🔒 /automod removeword** `<word>` — Remove filtered word\n"
                    "**🔒 /automod listwords** — List all filtered words\n"
                    "**🔒 /automod warnconfig** `<limit> <action> <min>` — Set auto-punish\n"
                    "**🔒 /automod logchannel** `<channel>` — Set mod-log channel\n"
                    "**🔒 /automod ignore** `<target>` — Bypass for channels/roles\n"
                    "**🔒 /automod status** — Show full configuration overview"
                )
            },
            "config": {
                "emoji": "⚙️",
                "title": "Configuration Commands",
                "color": discord.Color.blue(),
                "commands": (
                    "**🔒 /config announce_channel** `<channel>` — Set announcements\n"
                    "**🔒 /config rules_channel** `<channel>` — Set rules channel\n"
                    "**🔒 /log_setup** `<channel>` — Set up audit/log channel\n"
                    "**🔒 /set_botname** `<name>` — Change bot's nickname\n"
                    "**🔒 /set_logging** `<channel>` — Configure event logging\n"
                )
            },
            "tickets": {
                "emoji": "🎫",
                "title": "Ticket System Commands",
                "color": discord.Color.gold(),
                "commands": (
                    "**🔒 /ticket_setup** — Create the ticket panel\n"
                    "**🔒 /ticket_add** `<user>` — Add user to current ticket\n"
                    "**🔒 /ticket_remove** `<user>` — Remove user from ticket\n"
                    "**🔒 /ticket_rename** `<name>` — Rename ticket channel\n"
                )
            },
            "fun": {
                "emoji": "🎮",
                "title": "Fun Commands",
                "color": discord.Color.green(),
                "commands": (
                    "**/8ball** `<question>` — Ask the magic 8-ball\n"
                    "**/coinflip** — Flip a coin\n"
                    "**/roll** `<sides>` — Roll a dice\n"
                    "**/meme** — Fetch a random meme\n"
                    "**/poll** `<q> <o1> <o2>...` — Create a reaction poll\n"
                    "**/changelog** — View bot updates"
                )
            },
            "general": {
                "emoji": "ℹ️",
                "title": "General & Utility Commands",
                "color": discord.Color.from_rgb(88, 101, 242),
                "commands": (
                    "**/help** — Show this menu\n"
                    "**/ping** — Check bot latency\n"
                    "**/uptime** — Show bot uptime\n"
                    "**/botinfo** — View bot stats\n"
                    "**/membercount** — Show total members\n"
                    "**/invites** — Check user invites\n"
                    "**/calculate** `<expression>` — Math calculation"
                )
            }
        }

        if category not in categories:
            return self.build_overview_embed()

        cat = categories[category]
        embed = discord.Embed(
            title=f"{cat['emoji']} **{cat['title']}**",
            description=cat['commands'],
            color=cat['color']
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else discord.Embed.Empty)
        embed.set_footer(text="Ender Bot • Yaduvanshi1816_ • Use the dropdown to switch categories")
        embed.timestamp = discord.utils.utcnow()
        return embed

    @app_commands.command(name="help", description="Show the help menu with all available commands")
    @app_commands.describe(category="Choose a category to view specific commands")
    @app_commands.choices(category=[
        app_commands.Choice(name="🛡️ Moderation", value="moderation"),
        app_commands.Choice(name="🤖 AutoMod", value="automod"),
        app_commands.Choice(name="⚙️ Configuration", value="config"),
        app_commands.Choice(name="🎫 Tickets", value="tickets"),
        app_commands.Choice(name="🎮 Fun", value="fun"),
        app_commands.Choice(name="ℹ️ General", value="general"),
    ])
    async def help(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer()
        if category:
            embed = self.build_category_embed(category)
        else:
            embed = self.build_overview_embed()

        view = HelpDropdown(self)
        await interaction.followup.send(embed=embed, view=view)

class HelpDropdown(discord.ui.View):
    def __init__(self, cog: Help):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(HelpSelect(cog))

class HelpSelect(discord.ui.Select):
    def __init__(self, cog: Help):
        self.cog = cog
        options = [
            discord.SelectOption(label="Moderation", value="moderation", emoji="🛡️"),
            discord.SelectOption(label="AutoMod", value="automod", emoji="🤖"),
            discord.SelectOption(label="Configuration", value="config", emoji="⚙️"),
            discord.SelectOption(label="Tickets", value="tickets", emoji="🎫"),
            discord.SelectOption(label="Fun", value="fun", emoji="🎮"),
            discord.SelectOption(label="General", value="general", emoji="ℹ️"),
        ]
        super().__init__(
            placeholder="📌 Select a category...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        embed = self.cog.build_category_embed(self.values[0])
        await interaction.response.edit_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))