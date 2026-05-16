import discord
from discord import app_commands
from discord.ext import commands
import io
import datetime
import asyncio

# --- TICKET CONTROLS (Buttons inside the ticket) ---
class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # None makes the buttons persistent

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has a 'Staff' role (case insensitive)
        if not any(role.name.lower() == "staff" for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Only members with a 'Staff' role can claim tickets.", ephemeral=True)
        
        await interaction.response.send_message(f"🙋 **{interaction.user.display_name}** has claimed this ticket and will be assisting you shortly!")
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.grey, custom_id="transcript_ticket")
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        history_text = f"Ticket Transcript: {interaction.channel.name}\nGenerated on: {datetime.datetime.now()}\n"
        history_text += "-" * 30 + "\n"
        
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            time = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = message.content if message.content else "[No Text/Attachment]"
            history_text += f"[{time}] {message.author}: {content}\n"
        
        file = discord.File(io.BytesIO(history_text.encode()), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("📄 Transcript generated successfully.", file=file)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ This ticket will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- TICKET LAUNCHER (The initial button in the support channel) ---
class TicketLauncher(discord.ui.View):
    def __init__(self, category_id: int):
        super().__init__(timeout=None)
        self.category_id = category_id

    @discord.ui.button(label="📩 Open Support Ticket", style=discord.ButtonStyle.primary, custom_id="launcher_btn")
    async def launch(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = guild.get_channel(self.category_id)

        # Basic check to see if channel name already exists to prevent spam
        ticket_name = f"ticket-{interaction.user.name.lower()}".replace(" ", "-")
        existing_channel = discord.utils.get(guild.channels, name=ticket_name)
        
        if existing_channel:
            return await interaction.response.send_message(f"❌ You already have an open ticket: {existing_channel.mention}", ephemeral=True)

        # Set permissions: User & Bot see it, everyone else doesn't
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=ticket_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket for {interaction.user.id}"
        )

        await interaction.response.send_message(f"✅ Ticket created! Head over to {channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title="Ticket Support",
            description=f"Hello {interaction.user.mention}, thank you for reaching out.\nPlease describe your issue while waiting for staff.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use the buttons below to manage this ticket.")
        
        await channel.send(embed=embed, view=TicketControls())

# --- MAIN COG CLASS ---
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_setup", description="Deploys the ticket launcher in a specific channel")
    @app_commands.describe(channel="Where the button goes", category="Where tickets are created")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, category: discord.CategoryChannel):
        embed = discord.Embed(
            title="Support System",
            description="If you need assistance from our staff team, click the button below to start a private conversation.",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        await channel.send(embed=embed, view=TicketLauncher(category.id))
        await interaction.response.send_message("✅ Ticket system deployed successfully.", ephemeral=True)

    # --- EXTRA TICKET COMMANDS (To reach 100+ count) ---
    @app_commands.command(name="ticket_add", description="Add a member to an existing ticket")
    async def add_member(self, interaction: discord.Interaction, member: discord.Member):
        if "ticket-" not in interaction.channel.name:
            return await interaction.response.send_message("❌ This is not a ticket channel.", ephemeral=True)
        
        await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ {member.mention} has been added to the ticket.")

    @app_commands.command(name="ticket_remove", description="Remove a member from the ticket")
    async def remove_member(self, interaction: discord.Interaction, member: discord.Member):
        if "ticket-" not in interaction.channel.name:
            return await interaction.response.send_message("❌ This is not a ticket channel.", ephemeral=True)
        
        await interaction.channel.set_permissions(member, overwrite=None)
        await interaction.response.send_message(f"❌ {member.mention} has been removed from the ticket.")

    @app_commands.command(name="ticket_rename", description="Change the name of the ticket channel")
    async def rename(self, interaction: discord.Interaction, name: str):
        if "ticket-" not in interaction.channel.name:
            return await interaction.response.send_message("❌ This is not a ticket channel.", ephemeral=True)
        
        await interaction.channel.edit(name=f"ticket-{name}")
        await interaction.response.send_message(f"📝 Ticket renamed to **{name}**")

async def setup(bot):
    await bot.add_cog(Tickets(bot))