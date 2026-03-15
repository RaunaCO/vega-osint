import discord
from discord.ext import commands
import aiohttp
from datetime import datetime, timezone
from config.settings import GUILD_ID, OSINT_HITS_CHANNEL_ID

class OSINT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(guild_ids=[GUILD_ID], description="Search for a username across multiple social platforms")
    async def userrecon(self, ctx, username: str):
        await ctx.defer()

        platforms = {
            "GitHub":    f"https://github.com/{username}",
            "Instagram": f"https://www.instagram.com/{username}",
            "TikTok":    f"https://www.tiktok.com/@{username}",
            "Twitter/X": f"https://twitter.com/{username}",
            "Reddit":    f"https://www.reddit.com/user/{username}",
            "Pinterest": f"https://www.pinterest.com/{username}",
        }

        found = []
        not_found = []

        async with aiohttp.ClientSession() as session:
            for platform, url in platforms.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            found.append(f"🟢 **{platform}** — [view profile]({url})")
                        else:
                            not_found.append(f"🔴 {platform}")
                except:
                    not_found.append(f"⚫ {platform} (no response)")

        embed = discord.Embed(
            title=f"🔍 RECON — `{username}`",
            description="Digital presence analysis complete.",
            color=0x00ff41,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="✅ PROFILES FOUND", value="\n".join(found) if found else "None", inline=False)
        embed.add_field(name="❌ NOT FOUND", value="\n".join(not_found) if not_found else "None", inline=False)
        embed.set_footer(text="VEGA OSINT • Digital Reconnaissance Protocol")
        await ctx.respond(embed=embed)

        # Archive result in #osint-hits
        hits_channel = self.bot.get_channel(OSINT_HITS_CHANNEL_ID)
        if hits_channel:
            archive_embed = discord.Embed(
                title=f"📁 RECON ARCHIVED — `{username}`",
                color=0x00ff41,
                timestamp=datetime.now(timezone.utc)
            )
            archive_embed.add_field(name="✅ Found", value="\n".join(found) if found else "None", inline=False)
            archive_embed.add_field(name="❌ Not Found", value="\n".join(not_found) if not_found else "None", inline=False)
            archive_embed.set_footer(text=f"VEGA OSINT • Requested by {ctx.author.display_name}")
            await hits_channel.send(embed=archive_embed)

        admin = self.bot.cogs.get("VegaAdmin")
        if admin:
            admin.log(f"🔍 /userrecon: {username} — {len(found)} profiles found")

def setup(bot):
    bot.add_cog(OSINT(bot))