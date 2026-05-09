import discord
from discord.ext import commands
import os
import asyncio
from config import Config

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class SpiderMCBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None
        )
        self.ticket_category = None
        self.support_role = None
        self.ticket_count = 0
    
    async def setup_hook(self):
        await self.load_extension("cogs.setup")
        await self.load_extension("cogs.tickets")
        await self.load_extension("cogs.transcript")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        print(f"🕷️ SpiderMC Bot logged in as {self.user}")
        print(f"Bot ID: {self.user.id}")
        print("------")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="SpiderMC Tickets | !ticket setup"
            )
        )

bot = SpiderMCBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    """Reload a cog"""
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"✅ Reloaded `{extension}`")

bot.run(Config.TOKEN)