from redbot.core import commands, tasks, Config
import discord
import aiohttp
import json
import pytz
from datetime import datetime

class PinFill(commands.Cog):
    """A cog for fetching Elemental Storms timers from WoWhead."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel": None,
            "ping_user": None
        }
        self.config.register_guild(**default_guild)
        self.storm_check.start()

    def cog_unload(self):
        self.storm_check.cancel()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def elementalstorm(self, ctx, channel: discord.TextChannel, user: discord.Member = None):
        """Set the channel and optionally a user to ping for elemental storm spawns."""
        await self.config.guild(ctx.guild).channel.set(channel.id)
        if user:
            await self.config.guild(ctx.guild).ping_user.set(user.id)
        else:
            await self.config.guild(ctx.guild).ping_user.set(None)
        await ctx.send(f"Elemental storm spawn channel set to {channel.mention}. User to ping: {user.mention if user else 'None'}.")

    @tasks.loop(hours=3)
    async def storm_check(self):
        eastern = pytz.timezone('US/Eastern')
        current_time = datetime.now(eastern)
        if current_time.hour in [2, 5, 8, 11] and current_time.minute == 30:
            for guild in self.bot.guilds:
                channel_id = await self.config.guild(guild).channel()
                ping_user_id = await self.config.guild(guild).ping_user()
                if channel_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        url = "https://www.wowhead.com/today-in-wow"
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    html = await response.text()
                                    start_index = html.find('[{"class":"elemental-storm')
                                    end_index = html.find('}]', start_index) + 2
                                    if start_index != -1 and end_index != -1:
                                        json_str = html[start_index:end_index]
                                        try:
                                            data = json.loads(json_str)
                                            active_storms = []
                                            for item in data:
                                                if 'class' in item:
                                                    if 'tiw-upcoming' not in item['class']:
                                                        zone = item['name']
                                                        timer = item.get('ending', 'N/A')
                                                        element = item['class'].split('-')[-1].capitalize()
                                                        if (zone == "Ohn'ahran Plains" and element == "Fire") or \
                                                           (zone == "Thaldraszus" and element == "Air"):
                                                            active_storms.append(f"{zone} ({element}): {timer}")
                                            if active_storms:
                                                message = "Active Elemental Storms:\n"
                                                message += "\n".join(active_storms)
                                                if ping_user_id:
                                                    ping_user = guild.get_member(ping_user_id)
