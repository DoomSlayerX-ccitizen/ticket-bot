import discord
from discord.ext import commands

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def add(self, ctx, member: discord.Member):
        """Add a user to the ticket"""
        if "ticket-" not in ctx.channel.name:
            await ctx.send("❌ This is not a ticket channel!")
            return
        
        await ctx.channel.set_permissions(member, 
            read_messages=True,
            send_messages=True,
            attach_files=True
        )
        await ctx.send(f"✅ Added {member.mention} to the ticket.")
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def remove(self, ctx, member: discord.Member):
        """Remove a user from the ticket"""
        if "ticket-" not in ctx.channel.name:
            await ctx.send("❌ This is not a ticket channel!")
            return
        
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"✅ Removed {member.mention} from the ticket.")
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def rename(self, ctx, *, new_name: str):
        """Rename the ticket channel"""
        if "ticket-" not in ctx.channel.name:
            await ctx.send("❌ This is not a ticket channel!")
            return
        
        await ctx.channel.edit(name=f"ticket-{new_name}")
        await ctx.send(f"✅ Renamed ticket to `ticket-{new_name}`")

async def setup(bot):
    await bot.add_cog(Tickets(bot))