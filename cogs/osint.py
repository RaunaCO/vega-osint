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
                            found.append((platform, url))
                        else:
                            not_found.append(platform)
                except:
                    not_found.append(platform)

        found_text  = "\n".join([f"[{p}]({url})" for p, url in found]) if found else "*No profiles found*"
        absent_text = "  ·  ".join(not_found) if not_found else "—"

        embed = discord.Embed(
            title=f"Recon — {username}",
            color=0x336699,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name=f"Found ({len(found)})",      value=found_text,  inline=True)
        embed.add_field(name=f"Not found ({len(not_found)})", value=absent_text, inline=True)
        embed.set_footer(text=f"{len(found)}/{len(platforms)} platforms matched  ·  VEGA")
        await ctx.respond(embed=embed)

        hits_channel = self.bot.get_channel(OSINT_HITS_CHANNEL_ID)
        if hits_channel:
            archive_embed = discord.Embed(
                title=f"Recon archived — {username}",
                color=0x336699,
                timestamp=datetime.now(timezone.utc)
            )
            archive_embed.add_field(name=f"Found ({len(found)})",         value=found_text,  inline=True)
            archive_embed.add_field(name=f"Not found ({len(not_found)})", value=absent_text, inline=True)
            archive_embed.set_footer(text=f"requested by {ctx.author.display_name}  ·  VEGA")
            await hits_channel.send(embed=archive_embed)

        admin = self.bot.cogs.get("VegaAdmin")
        if admin:
            admin.log(f"🔍 /userrecon: {username} — {len(found)} profiles found")

def setup(bot):
    bot.add_cog(OSINT(bot))