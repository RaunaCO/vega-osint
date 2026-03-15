import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from config.settings import GUILD_ID, STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, CONFLICT_CHANNEL_ID, COMMAND_CENTER_ID
from utils.helpers import load_seen
import os
import json

SEEN_PATH = "data/seen.json"

class VegaAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now(timezone.utc)
        self.cycles_completed = 0
        self.last_scan = "Never"
        self.status_message = None
        self.logs_message = None
        self.command_center_message = None
        self.log_events = []
        self.recent_articles = []
        self.update_status.start()
        self.update_logs.start()
        self.update_command_center.start()

    def cog_unload(self):
        self.update_status.cancel()
        self.update_logs.cancel()
        self.update_command_center.cancel()

    def increment_cycle(self):
        """Increment the cycle counter and update last scan time."""
        self.cycles_completed += 1
        self.last_scan = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def log(self, event: str):
        """Add an event to the live log."""
        time = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.log_events.append(f"`{time}` {event}")
        if len(self.log_events) > 20:
            self.log_events.pop(0)

    def log_article(self, article: dict):
        """Register a new article for the command center display."""
        self.recent_articles.insert(0, article)
        if len(self.recent_articles) > 8:
            self.recent_articles.pop()

    def build_status_embed(self):
        """Build the live status panel embed."""
        now = datetime.now(timezone.utc)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        seen = load_seen()
        intel_cog = self.bot.cogs.get("Intel")
        monitor_active = intel_cog.monitor.is_running() if intel_cog else False
        interval = intel_cog.monitor.minutes if intel_cog else "N/A"

        embed = discord.Embed(
            title="⚡ VEGA OSINT — SYSTEM STATUS",
            description="```\nSYNTHETIC INTELLIGENCE PROTOCOL ACTIVE\n```",
            color=0x00ff41 if monitor_active else 0xff8800,
            timestamp=now
        )
        embed.add_field(name="🤖 System", value=f"```\n{'OPERATIONAL' if monitor_active else 'MONITOR PAUSED'}\n```", inline=False)
        embed.add_field(name="⏱️ Uptime", value=f"```\n{hours}h {minutes}m {seconds}s\n```", inline=True)
        embed.add_field(name="🔄 Cycles", value=f"```\n{self.cycles_completed}\n```", inline=True)
        embed.add_field(name="📰 In memory", value=f"```\n{len(seen)} articles\n```", inline=True)
        embed.add_field(name="📡 Monitor", value=f"```\n{'✅ Active' if monitor_active else '⏸️ Paused'}\n```", inline=True)
        embed.add_field(name="⏰ Interval", value=f"```\n{interval} min\n```", inline=True)
        embed.add_field(name="🕐 Last scan", value=f"```\n{self.last_scan}\n```", inline=True)
        embed.set_footer(text="VEGA OSINT • Auto-updated every 10 seconds")
        return embed

    def build_logs_embed(self):
        """Build the live activity log embed."""
        now = datetime.now(timezone.utc)
        events = "\n".join(self.log_events) if self.log_events else "`No activity recorded`"
        embed = discord.Embed(
            title="📋 VEGA — LIVE ACTIVITY LOG",
            description=events,
            color=0x2b2d31,
            timestamp=now
        )
        embed.set_footer(text="VEGA OSINT • Last 20 events — Updated every 10 seconds")
        return embed

    def build_command_center_embed(self):
        """Build the live global situation command center embed."""
        now = datetime.now(timezone.utc)

        active_regions = {}
        for a in self.recent_articles:
            region = a.get("region", "Global")
            level = a.get("level", "MEDIUM")
            if region not in active_regions or level == "CRITICAL":
                active_regions[region] = level

        level_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

        global_level = "CRITICAL" if "CRITICAL" in active_regions.values() else \
                       "HIGH" if "HIGH" in active_regions.values() else \
                       "MEDIUM" if active_regions else "LOW"

        embed = discord.Embed(
            title="🌍 VEGA — GLOBAL SITUATION LIVE",
            description=f"```\nGLOBAL LEVEL: {global_level}\n```",
            color={"CRITICAL": 0xff0000, "HIGH": 0xff6600, "MEDIUM": 0xffaa00, "LOW": 0x00ff41}.get(global_level, 0x0088ff),
            timestamp=now
        )

        regions_text = "\n".join([
            f"{level_emoji.get(level, '🟡')} **{region}** — {level}"
            for region, level in active_regions.items()
        ]) if active_regions else "*No recent activity*"

        embed.add_field(name="📡 ACTIVE REGIONS", value=regions_text, inline=False)

        articles_text = "\n".join([
            f"{level_emoji.get(a.get('level', 'MEDIUM'), '🟡')} [{a.get('time', '')}] {a.get('title', '')[:60]}..."
            for a in self.recent_articles[:5]
        ]) if self.recent_articles else "*Waiting for first intelligence cycle...*"

        embed.add_field(name="📰 LATEST ENTRIES", value=articles_text, inline=False)

        commands_text = (
            "`/scanfeed` — Scan sources now\n"
            "`/sitrep [topic]` — Generate situation report\n"
            "`/briefing [hours]` — Regional intelligence briefing\n"
            "`/analyze [text]` — AI text analysis\n"
            "`/summary [count]` — Summarize news channel\n"
            "`/userrecon [user]` — Username reconnaissance\n"
            "`/purge [channel]` — Clear channel messages\n"
            "`/clear` — Reset article memory\n"
            "`/pause [action]` — Pause/resume monitor\n"
            "`/interval [minutes]` — Change scan frequency"
        )
        embed.add_field(name="⚙️ AVAILABLE COMMANDS", value=commands_text, inline=False)
        embed.set_footer(text="VEGA OSINT • Updated every 30 seconds")
        return embed

    @tasks.loop(seconds=10)
    async def update_status(self):
        channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        if not channel:
            return
        embed = self.build_status_embed()
        try:
            if self.status_message:
                await self.status_message.edit(embed=embed)
            else:
                await channel.purge(limit=10)
                self.status_message = await channel.send(embed=embed)
        except discord.NotFound:
            self.status_message = await channel.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Status update error: {e}")

    @tasks.loop(seconds=10)
    async def update_logs(self):
        channel = self.bot.get_channel(LOGS_CHANNEL_ID)
        if not channel:
            return
        embed = self.build_logs_embed()
        try:
            if self.logs_message:
                await self.logs_message.edit(embed=embed)
            else:
                await channel.purge(limit=10)
                self.logs_message = await channel.send(embed=embed)
        except discord.NotFound:
            self.logs_message = await channel.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Logs update error: {e}")

    @tasks.loop(seconds=30)
    async def update_command_center(self):
        channel = self.bot.get_channel(COMMAND_CENTER_ID)
        if not channel:
            return
        embed = self.build_command_center_embed()
        try:
            if self.command_center_message:
                await self.command_center_message.edit(embed=embed)
            else:
                await channel.purge(limit=10)
                self.command_center_message = await channel.send(embed=embed)
        except discord.NotFound:
            self.command_center_message = await channel.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Command center update error: {e}")

    @update_status.before_loop
    async def before_status(self):
        await self.bot.wait_until_ready()

    @update_logs.before_loop
    async def before_logs(self):
        await self.bot.wait_until_ready()

    @update_command_center.before_loop
    async def before_command_center(self):
        await self.bot.wait_until_ready()

    @discord.slash_command(guild_ids=[GUILD_ID], description="Show current system status")
    async def status(self, ctx):
        await ctx.respond(embed=self.build_status_embed())

    @discord.slash_command(guild_ids=[GUILD_ID], description="Pause or resume the automatic monitor")
    async def pause(self, ctx, action: discord.Option(str, choices=["pause", "resume"])):
        intel_cog = self.bot.cogs.get("Intel")
        if not intel_cog:
            await ctx.respond("⚠️ **VEGA** — Intel module not found.")
            return
        if action == "pause":
            if intel_cog.monitor.is_running():
                intel_cog.monitor.cancel()
                await ctx.respond("⏸️ **VEGA** — Monitor **paused**.")
            else:
                await ctx.respond("⚠️ **VEGA** — Monitor was already paused.")
        elif action == "resume":
            if not intel_cog.monitor.is_running():
                intel_cog.monitor.start()
                await ctx.respond("▶️ **VEGA** — Monitor **resumed**.")
            else:
                await ctx.respond("⚠️ **VEGA** — Monitor was already active.")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Clear article memory and reset seen list")
    async def clear(self, ctx):
        if os.path.exists(SEEN_PATH):
            os.remove(SEEN_PATH)
        intel_cog = self.bot.cogs.get("Intel")
        if intel_cog:
            intel_cog.seen = set()
        embed = discord.Embed(
            title="🗑️ MEMORY CLEARED",
            description="Article history has been reset. Next cycle will scan all sources from scratch.",
            color=0xff8800,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA OSINT • Operation complete")
        await ctx.respond(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Change the monitor scan interval without restarting")
    async def interval(self, ctx, minutes: discord.Option(int, description="Minutes between cycles (minimum 2)")):
        if minutes < 2:
            await ctx.respond("⚠️ **VEGA** — Minimum interval is 2 minutes.")
            return
        intel_cog = self.bot.cogs.get("Intel")
        if not intel_cog:
            await ctx.respond("⚠️ **VEGA** — Intel module not found.")
            return
        intel_cog.monitor.change_interval(minutes=minutes)
        embed = discord.Embed(
            title="⏰ INTERVAL UPDATED",
            description=f"Monitor will now scan every **{minutes} minutes**.",
            color=0x00ff41,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA OSINT • Configuration updated")
        await ctx.respond(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Purge all messages from a channel")
    async def purge(self, ctx, channel: discord.Option(discord.TextChannel, description="Channel to clear")):
        await ctx.defer()
        protected = [STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, COMMAND_CENTER_ID]
        if channel.id in protected:
            await ctx.respond("⚠️ **VEGA** — That channel is protected.")
            return
        try:
            deleted = await channel.purge(limit=500)
            if channel.id == CONFLICT_CHANNEL_ID:
                intel_cog = self.bot.cogs.get("Intel")
                if intel_cog:
                    intel_cog.cycle_message = None
            embed = discord.Embed(
                title="🗑️ PURGE COMPLETE",
                description=f"Deleted **{len(deleted)} messages** from {channel.mention}.",
                color=0xff8800,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="VEGA OSINT • Operation complete")
            await ctx.respond(embed=embed)
            self.log(f"🗑️ Purge in {channel.name} — {len(deleted)} messages deleted")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Show active Vega modules")
    async def modules(self, ctx):
        with open("modules.json", "r") as f:
            config = json.load(f)["modules"]

        embed = discord.Embed(
            title="🧩 VEGA — SYSTEM MODULES",
            color=0x00ff41,
            timestamp=datetime.now(timezone.utc)
        )
        for name, data in config.items():
            status = "✅ Active" if data["enabled"] else "⏸️ Inactive"
            embed.add_field(
                name=f"{status} — `{name}`",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="VEGA OSINT • Edit modules.json to enable/disable modules")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(VegaAdmin(bot))
