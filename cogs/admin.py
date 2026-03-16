import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from config.settings import STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, COMMAND_CENTER_ID, VEGA_ERRORS_CHANNEL_ID
from utils.helpers import load_seen

class VegaAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time      = datetime.now(timezone.utc)
        self.cycles_completed = 0
        self.last_scan_time  = None   # datetime object for countdown
        self.last_scan       = "Never"
        self.sources_active  = 0
        self.articles_today  = 0
        self.status_message          = None
        self.logs_message            = None
        self.command_center_message  = None
        self.errors_message          = None
        self.log_events      = []
        self.error_log       = []
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
        self.last_scan_time   = datetime.now(timezone.utc)
        self.last_scan        = self.last_scan_time.strftime("%Y-%m-%d %H:%M:%S UTC")

    def set_scan_stats(self, sources: int, articles_today: int):
        """Called by intel.py after each cycle to update live stats."""
        self.sources_active = sources
        self.articles_today = articles_today

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

    def _next_scan_str(self) -> str:
        """Calculate time until next scan as a human-readable string."""
        intel_cog = self.bot.cogs.get("Intel")
        if not intel_cog or not intel_cog.monitor.is_running():
            return "Paused"
        if not self.last_scan_time:
            return "Pending"
        interval_minutes = intel_cog.monitor.minutes
        next_scan = self.last_scan_time + timedelta(minutes=interval_minutes)
        remaining = next_scan - datetime.now(timezone.utc)
        total_seconds = int(remaining.total_seconds())
        if total_seconds <= 0:
            return "Imminent"
        m, s = divmod(total_seconds, 60)
        return f"{m}m {s}s"

    def _error_rate_str(self) -> str:
        """Give a simple health indicator based on recent errors."""
        if not self.error_log:
            return "Healthy"
        if len(self.error_log) >= 5:
            return "Degraded"
        return "Minor issues"

    def build_status_embed(self):
        now    = datetime.now(timezone.utc)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        seen      = load_seen()
        intel_cog = self.bot.cogs.get("Intel")
        monitor_active = intel_cog.monitor.is_running() if intel_cog else False
        interval       = intel_cog.monitor.minutes if intel_cog else "N/A"

        embed = discord.Embed(
            title="System Status",
            color=0x00cc44 if monitor_active else 0xff8800,
            timestamp=now
        )
        embed.add_field(name="Status",       value="Operational" if monitor_active else "Monitor paused", inline=True)
        embed.add_field(name="Health",       value=self._error_rate_str(),                                inline=True)
        embed.add_field(name="Uptime",       value=f"{hours}h {minutes}m {seconds}s",                    inline=True)
        embed.add_field(name="Cycles",       value=str(self.cycles_completed),                            inline=True)
        embed.add_field(name="Articles today", value=str(self.articles_today),                            inline=True)
        embed.add_field(name="In memory",    value=f"{len(seen)} articles",                               inline=True)
        embed.add_field(name="Sources",      value=f"{self.sources_active} active",                       inline=True)
        embed.add_field(name="Interval",     value=f"{interval} min",                                     inline=True)
        embed.add_field(name="Next scan",    value=self._next_scan_str(),                                 inline=True)
        embed.set_footer(text=f"VEGA  ·  last scan: {self.last_scan}  ·  auto-refresh 10s")
        return embed

    def build_logs_embed(self):
        now    = datetime.now(timezone.utc)
        events = "\n".join(self.log_events) if self.log_events else "*No activity recorded*"
        embed  = discord.Embed(
            title="Activity Log",
            description=events,
            color=0x336699,
            timestamp=now
        )
        embed.set_footer(text="VEGA  ·  last 20 events  ·  auto-refresh 10s")
        return embed

    def build_errors_embed(self):
        now    = datetime.now(timezone.utc)
        errors = "\n".join(self.error_log) if self.error_log else "*No errors recorded*"
        embed  = discord.Embed(
            title="Error Monitor",
            description=errors,
            color=0xcc2200 if self.error_log else 0x00cc44,
            timestamp=now
        )
        embed.set_footer(text="VEGA  ·  last 10 errors  ·  auto-refresh 30s")
        return embed

    def build_command_center_embed(self):
        now = datetime.now(timezone.utc)

        # Derive global threat level from recent articles
        active_regions = {}
        for a in self.recent_articles:
            region = a.get("region", "Global")
            level  = a.get("level", "MEDIUM")
            if region not in active_regions or level == "CRITICAL":
                active_regions[region] = level

        level_badge  = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        global_level = (
            "CRITICAL" if "CRITICAL" in active_regions.values() else
            "HIGH"     if "HIGH"     in active_regions.values() else
            "MEDIUM"   if active_regions else "LOW"
        )
        global_color = {
            "CRITICAL": 0xcc2200, "HIGH": 0xdd5500,
            "MEDIUM":   0xccaa00, "LOW":  0x448844
        }.get(global_level, 0x336699)

        intel_cog      = self.bot.cogs.get("Intel")
        monitor_active = intel_cog.monitor.is_running() if intel_cog else False

        embed = discord.Embed(
            title="Global Situation",
            description=f"Threat level: **{global_level}**",
            color=global_color,
            timestamp=now
        )

        # System snapshot — compact inline fields
        embed.add_field(name="Monitor",       value="Active" if monitor_active else "Paused", inline=True)
        embed.add_field(name="Next scan",     value=self._next_scan_str(),                    inline=True)
        embed.add_field(name="Articles today",value=str(self.articles_today),                 inline=True)
        embed.add_field(name="Sources",       value=f"{self.sources_active} active",          inline=True)
        embed.add_field(name="Cycles",        value=str(self.cycles_completed),               inline=True)
        embed.add_field(name="Health",        value=self._error_rate_str(),                   inline=True)

        # Active regions
        regions_text = "\n".join([
            f"{level_badge.get(level, '⚪')} {region} — {level}"
            for region, level in active_regions.items()
        ]) if active_regions else "*No recent activity*"
        embed.add_field(name="Active Regions", value=regions_text, inline=False)

        # Latest entries
        articles_text = "\n".join([
            f"`{a.get('time', '--:--')}` {level_badge.get(a.get('level','MEDIUM'),'⚪')} {a.get('title','')[:60]}…"
            for a in self.recent_articles[:5]
        ]) if self.recent_articles else "*Waiting for first cycle…*"
        embed.add_field(name="Latest Entries", value=articles_text, inline=False)

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

def setup(bot):
    bot.add_cog(VegaAdmin(bot))