import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import json
import os
import asyncio

class TicketTypeView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.select(
        placeholder="Choose a category...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="General Support",
                description="Get help with general inquiries",
                emoji="🎫",
                value="general"
            ),
            discord.SelectOption(
                label="Purchase Support",
                description="Help with store purchases",
                emoji="🛒",
                value="purchase"
            ),
            discord.SelectOption(
                label="Player Report",
                description="Report a player",
                emoji="🚫",
                value="report"
            ),
            discord.SelectOption(
                label="Bug Report",
                description="Report technical issues",
                emoji="🐛",
                value="bug"
            )
        ],
        custom_id="ticket_type_select"
    )
    async def ticket_type_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        ticket_type = select.values[0]
        await self.create_ticket(interaction, ticket_type)
    
    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        # Load config
        try:
            with open(f"data/{interaction.guild_id}_config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message(
                "❌ Ticket system not set up yet! Ask an admin to run `!ticket setup`", 
                ephemeral=True
            )
            return
        
        category = interaction.guild.get_channel(config["category_id"])
        support_role = interaction.guild.get_role(config["support_role_id"])
        
        if not category or not support_role:
            await interaction.response.send_message(
                "❌ Configuration error. Please run setup again.", 
                ephemeral=True
            )
            return
        
        # Check if user already has an open ticket
        for channel in category.channels:
            if channel.name.startswith(f"ticket-{interaction.user.name.lower()}"):
                await interaction.response.send_message(
                    f"❌ You already have an open ticket: {channel.mention}", 
                    ephemeral=True
                )
                return
        
        # Create ticket channel
        ticket_number = len([c for c in category.channels if "ticket" in c.name]) + 1
        channel_name = f"ticket-{interaction.user.name.lower()}-{ticket_number}"
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            ),
            support_role: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True
            )
        }
        
        # Add bot permissions
        bot_member = interaction.guild.get_member(interaction.client.user.id)
        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True
            )
        
        ticket_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket for {interaction.user} | Type: {ticket_type}"
        )
        
        # Ticket type info
        type_info = {
            "general": {"name": "General Support", "emoji": "🎫", "color": 0x3498db},
            "purchase": {"name": "Purchase Support", "emoji": "🛒", "color": 0x2ecc71},
            "report": {"name": "Player Report", "emoji": "🚫", "color": 0xe74c3c},
            "bug": {"name": "Bug Report", "emoji": "🐛", "color": 0xf39c12}
        }
        
        info = type_info.get(ticket_type, type_info["general"])
        
        # Send ticket welcome message
        embed = discord.Embed(
            title=f"{info['emoji']} SpiderMC — {info['name']}",
            description=f"Welcome {interaction.user.mention}!\n\n"
                       f"You have opened a **{info['name']}** ticket.\n"
                       f"Please provide all necessary details below.\n\n"
                       f"{support_role.mention} will assist you shortly.",
            color=info['color']
        )
        embed.set_thumbnail(url="https://your-logo-url.com/spidermc_logo.png")
        embed.set_footer(text="SpiderMC Support | Use buttons below to manage")
        
        # Create claim/close buttons
        manage_view = TicketManageView(support_role)
        
        await ticket_channel.send(
            content=f"{interaction.user.mention} | {support_role.mention}",
            embed=embed,
            view=manage_view
        )
        
        # Send confirmation to user
        await interaction.response.send_message(
            f"✅ Ticket created: {ticket_channel.mention}", 
            ephemeral=True
        )

class TicketManageView(View):
    def __init__(self, support_role):
        super().__init__(timeout=None)
        self.support_role = support_role
        self.claimed_by = None
    
    @discord.ui.button(
        label="Claim", 
        style=discord.ButtonStyle.green,
        emoji="✋",
        custom_id="claim_ticket"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.support_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Only support team can claim tickets!", 
                ephemeral=True
            )
            return
        
        if self.claimed_by:
            await interaction.response.send_message(
                f"❌ Already claimed by {self.claimed_by.mention}", 
                ephemeral=True
            )
            return
        
        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        
        embed = discord.Embed(
            description=f"✋ Ticket claimed by {interaction.user.mention}",
            color=0x2ecc71
        )
        
        await interaction.message.edit(view=self)
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Ticket claimed!", ephemeral=True)
    
    @discord.ui.button(
        label="Close", 
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="close_ticket"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.support_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Only support team can close tickets!", 
                ephemeral=True
            )
            return
        
        # Confirm close
        confirm_view = CloseConfirmView()
        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=confirm_view,
            ephemeral=True
        )

class CloseConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @discord.ui.button(label="Yes, Close", style=discord.ButtonStyle.red, emoji="🔒")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)
        
        # Generate transcript
        transcript_cog = interaction.client.get_cog("Transcript")
        if transcript_cog:
            await transcript_cog.generate_transcript(interaction.channel)
        
        # Delete channel after delay
        await interaction.channel.send("🔒 This ticket will be closed in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Close cancelled.", ephemeral=True)

class CategorySelect(Select):
    def __init__(self, categories):
        options = [
            discord.SelectOption(
                label=cat.name[:25],
                value=str(cat.id),
                description=f"Channels: {len(cat.channels)}"
            ) for cat in categories[:25]
        ]
        super().__init__(
            placeholder="Select Ticket Category",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="category_select"
        )
        self.category = None
    
    async def callback(self, interaction: discord.Interaction):
        self.category = interaction.guild.get_channel(int(self.values[0]))
        self.view.category = self.category
        await interaction.response.send_message(
            f"✅ Category set to: {self.category.mention}", 
            ephemeral=True
        )

class RoleSelect(Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(
                label=role.name[:25],
                value=str(role.id),
                description=f"Members: {len(role.members)}"
            ) for role in roles[:25]
        ]
        super().__init__(
            placeholder="Select Support Role",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="role_select"
        )
        self.support_role = None
    
    async def callback(self, interaction: discord.Interaction):
        self.support_role = interaction.guild.get_role(int(self.values[0]))
        self.view.support_role = self.support_role
        await interaction.response.send_message(
            f"✅ Support role set to: {self.support_role.mention}", 
            ephemeral=True
        )

class SetupView(View):
    def __init__(self, bot, categories, roles):
        super().__init__(timeout=300)
        self.bot = bot
        self.category = None
        self.support_role = None
        
        # Add dropdowns dynamically
        self.add_item(CategorySelect(categories))
        self.add_item(RoleSelect(roles))
    
    @discord.ui.button(
        label="Confirm Setup", 
        style=discord.ButtonStyle.green,
        emoji="✅"
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.category or not self.support_role:
            await interaction.response.send_message(
                "❌ Please select both category and support role first!", 
                ephemeral=True
            )
            return
        
        # Save configuration
        config = {
            "guild_id": interaction.guild_id,
            "category_id": self.category.id,
            "support_role_id": self.support_role.id,
            "setup_channel_id": interaction.channel_id
        }
        
        # Save to JSON
        if not os.path.exists("data"):
            os.makedirs("data")
        
        with open(f"data/{interaction.guild_id}_config.json", "w") as f:
            json.dump(config, f, indent=4)
        
        self.bot.ticket_category = self.category
        self.bot.support_role = self.support_role
        
        # Create ticket panel embed
        embed = discord.Embed(
            title="🕷️ SpiderMC Support Portal",
            description="Welcome to the official SpiderMC support hub!\n\n"
                       "Select a category below to open a ticket.\n"
                       "Our support team will assist you shortly.",
            color=0xFF0000
        )
        embed.set_thumbnail(url="https://your-logo-url.com/spidermc_logo.png")
        embed.add_field(
            name="🎫 General Support", 
            value="Questions and general help", 
            inline=True
        )
        embed.add_field(
            name="🛒 Purchase Support", 
            value="Store and payment issues", 
            inline=True
        )
        embed.add_field(
            name="🚫 Player Report", 
            value="Report rule breakers", 
            inline=True
        )
        embed.add_field(
            name="🐛 Bug Report", 
            value="Technical issues", 
            inline=True
        )
        embed.set_footer(text="SpiderMC | New Era", icon_url="https://your-logo-url.com/spidermc_logo.png")
        
        # Create ticket type dropdown
        ticket_view = TicketTypeView(self.bot)
        
        await interaction.channel.send(embed=embed, view=ticket_view)
        await interaction.response.send_message(
            "✅ Setup complete! Ticket panel has been posted.", 
            ephemeral=True
        )
        self.stop()

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx, action: str = None):
        """Ticket system commands"""
        if action != "setup":
            embed = discord.Embed(
                title="🕷️ SpiderMC Ticket System",
                description="**Commands:**\n"
                           "`!ticket setup` - Setup ticket system\n"
                           "`!ticket config` - View current configuration",
                color=0xFF0000
            )
            embed.set_thumbnail(url="https://your-logo-url.com/spidermc_logo.png")
            await ctx.send(embed=embed)
            return
        
        # Check if server has categories and roles
        categories = [c for c in ctx.guild.categories if c.permissions_for(ctx.guild.me).manage_channels]
        roles = [r for r in ctx.guild.roles if r < ctx.guild.me.top_role and not r.is_default()]
        
        if not categories:
            await ctx.send("❌ No categories found! Create a category first for tickets.")
            return
        
        if not roles:
            await ctx.send("❌ No roles found! Create a support role first.")
            return
        
        # Setup command
        embed = discord.Embed(
            title="🕷️ SpiderMC Ticket Setup",
            description="Configure your ticket system below.\n\n"
                       "**Step 1:** Select the category where tickets will be created\n"
                       "**Step 2:** Select the support role\n"
                       "**Step 3:** Click Confirm Setup",
            color=0xFF0000
        )
        embed.set_thumbnail(url="https://your-logo-url.com/spidermc_logo.png")
        
        view = SetupView(self.bot, categories, roles)
        await ctx.send(embed=embed, view=view)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticket_config(self, ctx):
        """View ticket configuration"""
        try:
            with open(f"data/{ctx.guild.id}_config.json", "r") as f:
                config = json.load(f)
            
            category = ctx.guild.get_channel(config["category_id"])
            role = ctx.guild.get_role(config["support_role_id"])
            
            embed = discord.Embed(
                title="🕷️ SpiderMC Ticket Configuration",
                color=0xFF0000
            )
            embed.add_field(name="Category", value=category.mention if category else "Not found", inline=True)
            embed.add_field(name="Support Role", value=role.mention if role else "Not found", inline=True)
            embed.set_thumbnail(url="https://your-logo-url.com/spidermc_logo.png")
            
            await ctx.send(embed=embed)
        except FileNotFoundError:
            await ctx.send("❌ No configuration found. Run `!ticket setup` first.")

async def setup(bot):
    await bot.add_cog(Setup(bot))