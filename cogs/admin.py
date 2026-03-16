import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from config.settings import GUILD_ID, STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, CONFLICT_CHANNEL_ID, COMMAND_CENTER_ID, VEGA_ERRORS_CHANNEL_ID
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
        self.errors_message = None
        self.log_events = []
        self.error_log = []
        self.recent_articles = []
        self.update_status.start()
        self.update_logs.start()
        self.update_command_center.start()
        self.update_errors.start()

    def cog_unload(self):
        self.update_status.cancel()
        self.update_logs.cancel()
        self.update_command_center.cancel()
        self.update_errors.cancel()

    def increment_cycle(self):
        self.cycles_completed += 1
        self.last_scan = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def log(self, event: str):
        time = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.log_events.append(f"`{time}` {event}")
        if len(self.log_events) > 20:
            self.log_events.pop(0)

    def log_article(self, article: dict):
        self.recent_articles.insert(0, article)
        if len(self.recent_articles) > 8:
            self.recent_articles.pop()

    async def report_error(self, source: str, error: str):
        time = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.error_log.insert(0, f"`{time}` **{source}** — {error[:100]}")
        if len(self.error_log) > 10:
            self.error_log.pop()

    def build_status_embed(self):
        now = datetime.now(timezone.utc)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        seen = load_seen()
        intel_cog = self.bot.cogs.get("Intel")
        monitor_active = intel_cog.monitor.is_running() if intel_cog else False
        interval = intel_cog.monitor.minutes if intel_cog else "N/A"

        embed = discord.Embed(
            title="System Status",
            color=0x00cc44 if monitor_active else 0xff8800,
            timestamp=now
        )
        embed.add_field(name="Status",    value="Operational" if monitor_active else "Monitor paused", inline=True)
        embed.add_field(name="Uptime",    value=f"{hours}h {minutes}m {seconds}s",                     inline=True)
        embed.add_field(name="Cycles",    value=str(self.cycles_completed),                             inline=True)
        embed.add_field(name="In memory", value=f"{len(seen)} articles",                                inline=True)
        embed.add_field(name="Interval",  value=f"{interval} min",                                     inline=True)
        embed.add_field(name="Last scan", value=self.last_scan,                                         inline=True)
        embed.set_footer(text="VEGA  ·  auto-refresh 10s")
        return embed

    def build_logs_embed(self):
        now = datetime.now(timezone.utc)
        events = "\n".join(self.log_events) if self.log_events else "*No activity recorded*"
        embed = discord.Embed(
            title="Activity Log",
            description=events,
            color=0x336699,
            timestamp=now
        )
        embed.set_footer(text="VEGA  ·  last 20 events  ·  auto-refresh 10s")
        return embed

    def build_errors_embed(self):
        now = datetime.now(timezone.utc)
        errors = "\n".join(self.error_log) if self.error_log else "*No errors recorded*"
        embed = discord.Embed(
            title="Error Monitor",
            description=errors,
            color=0xcc2200 if self.error_log else 0x00cc44,
            timestamp=now
        )
        embed.set_footer(text="VEGA  ·  last 10 errors  ·  auto-refresh 30s")
        return embed

    def build_command_center_embed(self):
        now = datetime.now(timezone.utc)

        active_regions = {}
        for a in self.recent_articles:
            region = a.get("region", "Global")
            level  = a.get("level", "MEDIUM")
            if region not in active_regions or level == "CRITICAL":
                active_regions[region] = level

        badge = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        global_level = (
            "CRITICAL" if "CRITICAL" in active_regions.values() else
            "HIGH"     if "HIGH"     in active_regions.values() else
            "MEDIUM"   if active_regions else "LOW"
        )
        global_color = {"CRITICAL": 0xcc2200, "HIGH": 0xdd5500, "MEDIUM": 0xccaa00, "LOW": 0x448844}.get(global_level, 0x336699)

        embed = discord.Embed(
            title="Global Situation",
            description=f"Threat level: **{global_level}**",
            color=global_color,
            timestamp=now
        )

        # Active regions
        regions_text = "\n".join([
            f"{badge.get(level, '⚪')} {region} — {level}"
            for region, level in active_regions.items()
        ]) if active_regions else "*No recent activity*"
        embed.add_field(name="Active Regions", value=regions_text, inline=False)

        # Latest entries
        articles_text = "\n".join([
            f"`{a.get('time', '--:--')}` {badge.get(a.get('level','MEDIUM'),'⚪')} {a.get('title','')[:60]}…"
            for a in self.recent_articles[:5]
        ]) if self.recent_articles else "*Waiting for first cycle…*"
        embed.add_field(name="Latest Entries", value=articles_text, inline=False)

        # Commands — plain text, no block
        commands_text = (
            "`/scanfeed` `/sitrep` `/briefing` `/analyze` `/summary`\n"
            "`/userrecon` `/pause` `/interval` `/clear` `/purge`"
        )
        embed.add_field(name="Commands", value=commands_text, inline=False)
        embed.set_footer(text="VEGA  ·  auto-refresh 30s")
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
    async def update_errors(self):
        channel = self.bot.get_channel(VEGA_ERRORS_CHANNEL_ID)
        if not channel:
            return
        embed = self.build_errors_embed()
        try:
            if self.errors_message:
                await self.errors_message.edit(embed=embed)
            else:
                await channel.purge(limit=10)
                self.errors_message = await channel.send(embed=embed)
        except discord.NotFound:
            self.errors_message = await channel.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Error monitor update error: {e}")

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

    @update_errors.before_loop
    async def before_errors(self):
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
                await ctx.respond("Monitor paused.")
            else:
                await ctx.respond("Monitor was already paused.")
        elif action == "resume":
            if not intel_cog.monitor.is_running():
                intel_cog.monitor.start()
                await ctx.respond("Monitor resumed.")
            else:
                await ctx.respond("Monitor was already active.")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Clear article memory and reset seen list")
    async def clear(self, ctx):
        if os.path.exists(SEEN_PATH):
            os.remove(SEEN_PATH)
        intel_cog = self.bot.cogs.get("Intel")
        if intel_cog:
            intel_cog.seen = set()
        embed = discord.Embed(
            title="Memory Cleared",
            description="Article history reset. Next cycle will scan all sources from scratch.",
            color=0xff8800,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA  ·  operation complete")
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
            title="Interval Updated",
            description=f"Monitor will scan every **{minutes} minutes**.",
            color=0x00cc44,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA  ·  configuration updated")
        await ctx.respond(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Purge all messages from a channel")
    async def purge(self, ctx, channel: discord.Option(discord.TextChannel, description="Channel to clear")):
        await ctx.defer()
        protected = [STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, COMMAND_CENTER_ID, VEGA_ERRORS_CHANNEL_ID]
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
                title="Purge Complete",
                description=f"Deleted **{len(deleted)} messages** from {channel.mention}.",
                color=0xff8800,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="VEGA  ·  operation complete")
            await ctx.respond(embed=embed)
            self.log(f"🗑️ Purge in {channel.name} — {len(deleted)} messages deleted")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Show active Vega modules")
    async def modules(self, ctx):
        with open("modules.json", "r") as f:
            config = json.load(f)["modules"]

        embed = discord.Embed(
            title="System Modules",
            color=0x336699,
            timestamp=datetime.now(timezone.utc)
        )
        for name, data in config.items():
            status = "Active" if data["enabled"] else "Inactive"
            embed.add_field(
                name=f"{name}  ·  {status}",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="VEGA  ·  edit modules.json to enable/disable")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(VegaAdmin(bot))