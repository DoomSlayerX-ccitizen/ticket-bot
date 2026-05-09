import discord
from discord.ext import commands
from datetime import datetime
import io

class Transcript(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def generate_transcript(self, channel: discord.TextChannel):
        """Generate HTML transcript of ticket"""
        messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            messages.append(message)
        
        # Create HTML transcript
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>SpiderMC Ticket Transcript - {channel.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; padding: 20px; }}
        .header {{ text-align: center; padding: 20px; background: #FF0000; border-radius: 10px; margin-bottom: 20px; }}
        .message {{ background: #2d2d2d; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .author {{ color: #FF0000; font-weight: bold; }}
        .timestamp {{ color: #888; font-size: 0.8em; }}
        .content {{ margin-top: 5px; }}
        img {{ max-width: 400px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ SpiderMC Ticket Transcript</h1>
        <p>Channel: {channel.name}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        for msg in messages:
            content = msg.content.replace("<", "&lt;").replace(">", "&gt;")
            if msg.embeds:
                content += " [Embed]"
            if msg.attachments:
                content += f" [Attachment: {msg.attachments[0].filename}]"
            
            html_content += f"""
    <div class="message">
        <span class="author">{msg.author.name}</span>
        <span class="timestamp">{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}</span>
        <div class="content">{content}</div>
    </div>
"""
        
        html_content += "</body></html>"
        
        # Send transcript to log channel or user
        transcript_file = discord.File(
            io.BytesIO(html_content.encode()),
            filename=f"{channel.name}_transcript.html"
        )
        
        # Try to send to a log channel if exists
        log_channel = discord.utils.get(channel.guild.text_channels, name="ticket-logs")
        if log_channel:
            embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=f"Ticket `{channel.name}` has been closed.",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed, file=transcript_file)
        
        return transcript_file

async def setup(bot):
    await bot.add_cog(Transcript(bot))