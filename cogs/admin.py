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
        """Log error to live panel."""
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
        status_str = "OPERATIONAL" if monitor_active else "MONITOR PAUSED"

        # Single clean monospace block — no individual fields
        block = (
            f"```\n"
            f"STATUS    : {status_str}\n"
            f"UPTIME    : {hours}h {minutes}m {seconds}s\n"
            f"CYCLES    : {self.cycles_completed}\n"
            f"IN MEMORY : {len(seen)} articles\n"
            f"MONITOR   : {'ACTIVE' if monitor_active else 'PAUSED'}\n"
            f"INTERVAL  : {interval} min\n"
            f"LAST SCAN : {self.last_scan}\n"
            f"```"
        )

        embed = discord.Embed(
            title="VEGA // SYSTEM STATUS",
            description=block,
            color=0x00ff41 if monitor_active else 0xff8800,
            timestamp=now
        )
        embed.set_footer(text="VEGA // auto-refresh 10s")
        return embed

    def build_logs_embed(self):
        now = datetime.now(timezone.utc)
        events = "\n".join(self.log_events) if self.log_events else "`— no activity recorded —`"
        embed = discord.Embed(
            title="VEGA // ACTIVITY LOG",
            description=events,
            color=0x1a1a2e,
            timestamp=now
        )
        embed.set_footer(text="VEGA // last 20 events // auto-refresh 10s")
        return embed

    def build_errors_embed(self):
        now = datetime.now(timezone.utc)
        errors = "\n".join(self.error_log) if self.error_log else "`— no errors recorded —`"
        embed = discord.Embed(
            title="VEGA // ERROR MONITOR",
            description=errors,
            color=0xff0000 if self.error_log else 0x00ff41,
            timestamp=now
        )
        embed.set_footer(text="VEGA // last 10 errors // auto-refresh 30s")
        return embed

    def build_command_center_embed(self):
        now = datetime.now(timezone.utc)

        active_regions = {}
        for a in self.recent_articles:
            region = a.get("region", "Global")
            level = a.get("level", "MEDIUM")
            if region not in active_regions or level == "CRITICAL":
                active_regions[region] = level

        level_indicator = {"CRITICAL": "◈ CRITICAL", "HIGH": "◈ HIGH", "MEDIUM": "◈ MEDIUM", "LOW": "◈ LOW"}

        global_level = "CRITICAL" if "CRITICAL" in active_regions.values() else \
                       "HIGH" if "HIGH" in active_regions.values() else \
                       "MEDIUM" if active_regions else "LOW"

        global_color = {"CRITICAL": 0xff0000, "HIGH": 0xff4400, "MEDIUM": 0xffaa00, "LOW": 0x00ff41}.get(global_level, 0x1a1a2e)

        embed = discord.Embed(
            title="VEGA // GLOBAL SITUATION",
            description=f"```\nGLOBAL THREAT LEVEL : {global_level}\n```",
            color=global_color,
            timestamp=now
        )

        # Active regions — clean, no emoji
        regions_text = "\n".join([
            f"`{level_indicator.get(level, level)}`  {region}"
            for region, level in active_regions.items()
        ]) if active_regions else "*— no recent activity —*"

        embed.add_field(name="ACTIVE REGIONS", value=regions_text, inline=False)

        # Latest entries — compact
        articles_text = "\n".join([
            f"`[{a.get('time', '--:--')}]` `{a.get('level', 'MED'):<8}` {a.get('title', '')[:55]}..."
            for a in self.recent_articles[:5]
        ]) if self.recent_articles else "*— waiting for first cycle —*"

        embed.add_field(name="LATEST ENTRIES", value=articles_text, inline=False)

        # Commands — monospace block
        commands_block = (
            "```\n"
            "/scanfeed           scan sources now\n"
            "/sitrep [topic]     situation report\n"
            "/briefing [hours]   regional briefing\n"
            "/analyze [text]     AI text analysis\n"
            "/summary [count]    summarize feed\n"
            "/userrecon [user]   username recon\n"
            "/pause [action]     pause/resume monitor\n"
            "/interval [min]     change scan frequency\n"
            "/clear              reset article memory\n"
            "/purge [channel]    clear channel\n"
            "```"
        )
        embed.add_field(name="COMMANDS", value=commands_block, inline=False)
        embed.set_footer(text="VEGA // auto-refresh 30s")
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
            title="MEMORY CLEARED",
            description="```\nArticle history reset.\nNext cycle will scan all sources from scratch.\n```",
            color=0xff8800,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA // operation complete")
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
            title="INTERVAL UPDATED",
            description=f"```\nMonitor interval set to {minutes} minutes.\n```",
            color=0x00ff41,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA // configuration updated")
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
                title="PURGE COMPLETE",
                description=f"```\nDeleted {len(deleted)} messages from #{channel.name}\n```",
                color=0xff8800,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="VEGA // operation complete")
            await ctx.respond(embed=embed)
            self.log(f"🗑️ Purge in {channel.name} — {len(deleted)} messages deleted")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Show active Vega modules")
    async def modules(self, ctx):
        with open("modules.json", "r") as f:
            config = json.load(f)["modules"]

        lines = []
        for name, data in config.items():
            state = "ACTIVE  " if data["enabled"] else "INACTIVE"
            lines.append(f"  {state}  {name:<12}  {data['description'][:45]}")

        block = "```\n" + "\n".join(lines) + "\n```"

        embed = discord.Embed(
            title="VEGA // SYSTEM MODULES",
            description=block,
            color=0x1a1a2e,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA // edit modules.json to enable/disable")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(VegaAdmin(bot))