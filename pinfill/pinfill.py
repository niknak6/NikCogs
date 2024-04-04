from redbot.core import commands
import discord
import aiohttp
import json
import time
import asyncio

class PinFill(commands.Cog):
    """A cog for fetching Elemental Storms timers from WoWhead."""

    def __init__(self, bot):
        self.bot = bot
        self.auto_check_task = None
        self.channel = None
        self.user_to_ping = None

    async def auto_check_elemental_storms(self):
        while True:
            active_storms = await self.get_active_storms()
            if active_storms:
                message = "Active Elemental Storms:\n"
                message += "\n".join(active_storms)
                if self.user_to_ping:
                    message = f"{self.user_to_ping.mention}\n{message}"
                await self.channel.send(message)
            await asyncio.sleep(1800)  # 30 minutes!

    async def get_active_storms(self):
        url = "https://www.wowhead.com/today-in-wow?_=" + str(int(time.time()))
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
                            return active_storms
                        except json.JSONDecodeError as e:
                            return []
                    else:
                        return []
                else:
                    return []

    @commands.command()
    async def elementalstorm(self, ctx, channel: discord.TextChannel = None, user: discord.Member = None):
        """Fetches and displays upcoming Elemental Storms timers."""
        if channel and user:
            self.channel = channel
            self.user_to_ping = user
            if not self.auto_check_task or self.auto_check_task.done():
                self.auto_check_task = self.bot.loop.create_task(self.auto_check_elemental_storms())
            await ctx.send(f"Started auto-checking for Elemental Storms in {channel.mention} and pinging {user.mention}.")
        else:
            active_storms = await self.get_active_storms()
            if active_storms:
                message = "Active Elemental Storms:\n"
                message += "\n".join(active_storms)
                await ctx.send(message)
            else:
                await ctx.send("No active Elemental Storms found for the specified zones and elements.")

    @commands.command()
    async def stopelementalstorm(self, ctx):
        """Stops the auto-checking of Elemental Storms."""
        if self.auto_check_task and not self.auto_check_task.done():
            self.auto_check_task.cancel()
            self.channel = None
            self.user_to_ping = None
            await ctx.send("Stopped auto-checking for Elemental Storms.")
        else:
            await ctx.send("Auto-checking for Elemental Storms is not currently running.")

async def setup(bot):
    bot.add_cog(PinFill(bot))
