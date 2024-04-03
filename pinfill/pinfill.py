from redbot.core import commands
import discord
import aiohttp
import json
import time

class PinFill(commands.Cog):
    """A cog for fetching Elemental Storms timers from WoWhead."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def elementalstorm(self, ctx):
        """Fetches and displays upcoming Elemental Storms timers."""
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
                            upcoming_storms = []
                            for item in data:
                                if 'class' in item:
                                    if 'tiw-upcoming' not in item['class']:
                                        zone = item['name']
                                        timer = item.get('ending', 'N/A')
                                        active_storms.append(f"{zone}: {timer}")
                                    else:
                                        upcoming_storms.append(item['name'])
                            message = ""
                            if active_storms:
                                message += "Active Elemental Storms:\n"
                                message += "\n".join(active_storms) + "\n\n"
                            if upcoming_storms:
                                message += "Upcoming Elemental Storms:\n"
                                message += "\n".join(upcoming_storms)
                            if not message:
                                await ctx.send("No active or upcoming Elemental Storms found.")
                            else:
                                await ctx.send(message)
                        except json.JSONDecodeError as e:
                            await ctx.send("Failed to parse the Elemental Storms data.")
                    else:
                        await ctx.send("Failed to find the Elemental Storms data on WoWhead.")
                else:
                    await ctx.send(f"Failed to fetch data from WoWhead. Status Code: {response.status}")

async def setup(bot):
    bot.add_cog(PinFill(bot))
