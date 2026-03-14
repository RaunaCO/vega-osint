import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from config.settings import GUILD_ID, STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, CONFLICT_CHANNEL_ID, COMMAND_CENTER_ID
from utils.helpers import cargar_vistos
import os

VISTOS_PATH = "data/vistos.json"

class VegaAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inicio = datetime.now(timezone.utc)
        self.ciclos_completados = 0
        self.ultimo_escaneo = "Nunca"
        self.mensaje_status = None
        self.mensaje_logs = None
        self.mensaje_command_center = None
        self.log_eventos = []
        self.ultimas_noticias = []
        self.actualizar_status.start()
        self.actualizar_logs.start()
        self.actualizar_command_center.start()

    def cog_unload(self):
        self.actualizar_status.cancel()
        self.actualizar_logs.cancel()
        self.actualizar_command_center.cancel()

    def incrementar_ciclo(self):
        self.ciclos_completados += 1
        self.ultimo_escaneo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def registrar(self, evento: str):
        hora = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.log_eventos.append(f"`{hora}` {evento}")
        if len(self.log_eventos) > 20:
            self.log_eventos.pop(0)

    def registrar_noticia(self, noticia: dict):
        self.ultimas_noticias.insert(0, noticia)
        if len(self.ultimas_noticias) > 8:
            self.ultimas_noticias.pop()

    def construir_embed_status(self):
        ahora = datetime.now(timezone.utc)
        uptime = ahora - self.inicio
        horas, resto = divmod(int(uptime.total_seconds()), 3600)
        minutos, segundos = divmod(resto, 60)
        vistos = cargar_vistos()
        intel_cog = self.bot.cogs.get("Intel")
        monitor_activo = intel_cog.monitor.is_running() if intel_cog else False
        intervalo = intel_cog.monitor.minutes if intel_cog else "N/A"

        embed = discord.Embed(
            title="⚡ VEGA OSINT — PANEL DE ESTADO",
            description="```\nPROTOCOLO DE INTELIGENCIA SINTÉTICA ACTIVO\n```",
            color=0x00ff41 if monitor_activo else 0xff8800,
            timestamp=ahora
        )
        embed.add_field(name="🤖 Sistema", value=f"```\n{'OPERATIVO' if monitor_activo else 'MONITOR PAUSADO'}\n```", inline=False)
        embed.add_field(name="⏱️ Uptime", value=f"```\n{horas}h {minutos}m {segundos}s\n```", inline=True)
        embed.add_field(name="🔄 Ciclos", value=f"```\n{self.ciclos_completados}\n```", inline=True)
        embed.add_field(name="📰 En memoria", value=f"```\n{len(vistos)} noticias\n```", inline=True)
        embed.add_field(name="📡 Monitor", value=f"```\n{'✅ Activo' if monitor_activo else '⏸️ Pausado'}\n```", inline=True)
        embed.add_field(name="⏰ Intervalo", value=f"```\n{intervalo} min\n```", inline=True)
        embed.add_field(name="🕐 Último escaneo", value=f"```\n{self.ultimo_escaneo}\n```", inline=True)
        embed.set_footer(text="VEGA OSINT • Actualizado cada 10 segundos")
        return embed

    def construir_embed_logs(self):
        ahora = datetime.now(timezone.utc)
        eventos = "\n".join(self.log_eventos) if self.log_eventos else "`Sin actividad registrada`"
        embed = discord.Embed(
            title="📋 VEGA — LOG DE ACTIVIDAD",
            description=eventos,
            color=0x2b2d31,
            timestamp=ahora
        )
        embed.set_footer(text="VEGA OSINT • Últimos 20 eventos — Actualizado cada 10 segundos")
        return embed

    def construir_embed_command_center(self):
        ahora = datetime.now(timezone.utc)

        # Regiones activas de las últimas noticias
        regiones_activas = {}
        for n in self.ultimas_noticias:
            region = n.get("region", "Global")
            nivel = n.get("nivel", "MEDIO")
            if region not in regiones_activas or nivel == "CRÍTICO":
                regiones_activas[region] = nivel

        niveles_emoji = {"CRÍTICO": "🔴", "ALTO": "🟠", "MEDIO": "🟡", "BAJO": "🟢"}

        # Estado global
        nivel_global = "CRÍTICO" if "CRÍTICO" in regiones_activas.values() else \
                       "ALTO" if "ALTO" in regiones_activas.values() else \
                       "MEDIO" if regiones_activas else "BAJO"

        embed = discord.Embed(
            title="🌍 VEGA — SITUACIÓN GLOBAL EN VIVO",
            description=f"```\nNIVEL GLOBAL: {nivel_global}\n```",
            color={"CRÍTICO": 0xff0000, "ALTO": 0xff6600, "MEDIO": 0xffaa00, "BAJO": 0x00ff41}.get(nivel_global, 0x0088ff),
            timestamp=ahora
        )

        # Regiones activas
        if regiones_activas:
            regiones_texto = "\n".join([
                f"{niveles_emoji.get(nivel, '🟡')} **{region}** — {nivel}"
                for region, nivel in regiones_activas.items()
            ])
        else:
            regiones_texto = "*Sin actividad reciente*"

        embed.add_field(name="📡 REGIONES ACTIVAS", value=regiones_texto, inline=False)

        # Últimas noticias
        if self.ultimas_noticias:
            noticias_texto = "\n".join([
                f"{niveles_emoji.get(n.get('nivel', 'MEDIO'), '🟡')} [{n.get('hora', '')}] {n.get('titulo', '')[:60]}..."
                for n in self.ultimas_noticias[:5]
            ])
        else:
            noticias_texto = "*Esperando primer ciclo de inteligencia...*"

        embed.add_field(name="📰 ÚLTIMAS ENTRADAS", value=noticias_texto, inline=False)

        # Comandos disponibles
        comandos = (
            "`/scanfeed` — Escanear fuentes ahora\n"
            "`/sitrep` — Generar informe de situación\n"
            "`/briefing` — Resumen de las últimas horas\n"
            "`/analizar` — Analizar texto con IA\n"
            "`/resumen` — Resumir canal de noticias\n"
            "`/userrecon` — Reconocimiento de usuario\n"
            "`/purgar` — Limpiar canal\n"
            "`/limpiar` — Resetear memoria\n"
            "`/pausar` — Pausar/reanudar monitor\n"
            "`/intervalo` — Cambiar frecuencia"
        )
        embed.add_field(name="⚙️ COMANDOS DISPONIBLES", value=comandos, inline=False)
        embed.set_footer(text="VEGA OSINT • Actualizado cada 30 segundos")
        return embed

    @tasks.loop(seconds=10)
    async def actualizar_status(self):
        canal = self.bot.get_channel(STATUS_CHANNEL_ID)
        if not canal:
            return
        embed = self.construir_embed_status()
        try:
            if self.mensaje_status:
                await self.mensaje_status.edit(embed=embed)
            else:
                await canal.purge(limit=10)
                self.mensaje_status = await canal.send(embed=embed)
        except discord.NotFound:
            self.mensaje_status = await canal.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Error actualizando status: {e}")

    @tasks.loop(seconds=10)
    async def actualizar_logs(self):
        canal = self.bot.get_channel(LOGS_CHANNEL_ID)
        if not canal:
            return
        embed = self.construir_embed_logs()
        try:
            if self.mensaje_logs:
                await self.mensaje_logs.edit(embed=embed)
            else:
                await canal.purge(limit=10)
                self.mensaje_logs = await canal.send(embed=embed)
        except discord.NotFound:
            self.mensaje_logs = await canal.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Error actualizando logs: {e}")

    @tasks.loop(seconds=30)
    async def actualizar_command_center(self):
        canal = self.bot.get_channel(COMMAND_CENTER_ID)
        if not canal:
            return
        embed = self.construir_embed_command_center()
        try:
            if self.mensaje_command_center:
                await self.mensaje_command_center.edit(embed=embed)
            else:
                await canal.purge(limit=10)
                self.mensaje_command_center = await canal.send(embed=embed)
        except discord.NotFound:
            self.mensaje_command_center = await canal.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Error actualizando command center: {e}")

    @actualizar_status.before_loop
    async def before_status(self):
        await self.bot.wait_until_ready()

    @actualizar_logs.before_loop
    async def before_logs(self):
        await self.bot.wait_until_ready()

    @actualizar_command_center.before_loop
    async def before_command_center(self):
        await self.bot.wait_until_ready()

    @discord.slash_command(guild_ids=[GUILD_ID], description="Muestra el estado actual de Vega")
    async def estado(self, ctx):
        await ctx.respond(embed=self.construir_embed_status())

    @discord.slash_command(guild_ids=[GUILD_ID], description="Pausa o reanuda el monitor automático")
    async def pausar(self, ctx, accion: discord.Option(str, choices=["pausar", "reanudar"])):
        intel_cog = self.bot.cogs.get("Intel")
        if not intel_cog:
            await ctx.respond("⚠️ **VEGA** — Módulo Intel no encontrado.")
            return
        if accion == "pausar":
            if intel_cog.monitor.is_running():
                intel_cog.monitor.cancel()
                await ctx.respond("⏸️ **VEGA** — Monitor **pausado**.")
            else:
                await ctx.respond("⚠️ **VEGA** — El monitor ya estaba pausado.")
        elif accion == "reanudar":
            if not intel_cog.monitor.is_running():
                intel_cog.monitor.start()
                await ctx.respond("▶️ **VEGA** — Monitor **reanudado**.")
            else:
                await ctx.respond("⚠️ **VEGA** — El monitor ya estaba activo.")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Limpia el historial de noticias vistas")
    async def limpiar(self, ctx):
        if os.path.exists(VISTOS_PATH):
            os.remove(VISTOS_PATH)
        intel_cog = self.bot.cogs.get("Intel")
        if intel_cog:
            intel_cog.vistos = set()
        embed = discord.Embed(
            title="🗑️ MEMORIA LIMPIADA",
            description="El historial fue eliminado. El próximo ciclo escaneará desde cero.",
            color=0xff8800,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA OSINT • Operación completada")
        await ctx.respond(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Cambia el intervalo del monitor sin reiniciar")
    async def intervalo(self, ctx, minutos: discord.Option(int, description="Minutos entre ciclos (mínimo 2)")):
        if minutos < 2:
            await ctx.respond("⚠️ **VEGA** — El intervalo mínimo es 2 minutos.")
            return
        intel_cog = self.bot.cogs.get("Intel")
        if not intel_cog:
            await ctx.respond("⚠️ **VEGA** — Módulo Intel no encontrado.")
            return
        intel_cog.monitor.change_interval(minutes=minutos)
        embed = discord.Embed(
            title="⏰ INTERVALO ACTUALIZADO",
            description=f"El monitor escaneará cada **{minutos} minutos**.",
            color=0x00ff41,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="VEGA OSINT • Configuración actualizada")
        await ctx.respond(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Purga todos los mensajes de un canal")
    async def purgar(self, ctx, canal: discord.Option(discord.TextChannel, description="Canal a limpiar")):
        await ctx.defer()
        canales_protegidos = [STATUS_CHANNEL_ID, LOGS_CHANNEL_ID, COMMAND_CENTER_ID]
        if canal.id in canales_protegidos:
            await ctx.respond("⚠️ **VEGA** — Ese canal está protegido.")
            return
        try:
            borrados = await canal.purge(limit=500)
            if canal.id == CONFLICT_CHANNEL_ID:
                intel_cog = self.bot.cogs.get("Intel")
                if intel_cog:
                    intel_cog.mensaje_ciclo = None
            embed = discord.Embed(
                title="🗑️ PURGA COMPLETADA",
                description=f"Se eliminaron **{len(borrados)} mensajes** de {canal.mention}.",
                color=0xff8800,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="VEGA OSINT • Operación completada")
            await ctx.respond(embed=embed)
            self.registrar(f"🗑️ Purga en {canal.name} — {len(borrados)} mensajes")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

def setup(bot):
    bot.add_cog(VegaAdmin(bot))